from fastapi.testclient import TestClient


def create_group(client: TestClient, members=("Ana", "Luis", "Marta")) -> tuple[int, dict[str, int]]:
    """Creates a group and returns its id and a {name: member id} map."""
    response = client.post("/api/groups", json={"name": "Piso Lavapiés", "members": list(members)})
    assert response.status_code == 201
    body = response.json()
    return body["id"], {member["name"]: member["id"] for member in body["members"]}


def add_equal_expense(
    client: TestClient, group_id: int, amount: int, paid_by: int, member_ids: list[int]
) -> dict:
    response = client.post(
        f"/api/groups/{group_id}/expenses",
        json={
            "description": "Cena",
            "amountCents": amount,
            "paidBy": paid_by,
            "split": {"mode": "equal", "memberIds": member_ids},
        },
    )
    assert response.status_code == 201
    return response.json()


def post_payment(client: TestClient, group_id: int, from_id: int, to_id: int, amount: int):
    return client.post(
        f"/api/groups/{group_id}/payments",
        json={"fromMemberId": from_id, "toMemberId": to_id, "amountCents": amount},
    )


def get_settlements(client: TestClient, group_id: int) -> list[tuple[str, str, int]]:
    """Settlements as (who pays, who receives, cents), easier to compare in asserts."""
    settlements = client.get(f"/api/groups/{group_id}/settlements").json()
    return [(s["fromName"], s["toName"], s["amountCents"]) for s in settlements]


# ---------- Groups and members ----------


def test_demo_data_is_not_seeded_into_the_test_database(client):
    assert client.get("/api/groups").json() == []


def test_create_group(client):
    response = client.post("/api/groups", json={"name": "Piso Lavapiés", "members": ["Ana", "Luis"]})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Piso Lavapiés"
    assert body["currency"] == "EUR"
    assert [member["name"] for member in body["members"]] == ["Ana", "Luis"]
    assert body["expenses"] == []
    assert body["payments"] == []


def test_group_needs_two_different_members(client):
    one_member = client.post("/api/groups", json={"name": "Solo", "members": ["Ana"]})
    assert one_member.status_code == 422
    assert one_member.json() == {"detail": "Un grupo necesita al menos 2 personas"}

    repeated = client.post("/api/groups", json={"name": "Repes", "members": ["Ana", "ana "]})
    assert repeated.status_code == 422
    assert repeated.json() == {"detail": "Hay nombres repetidos en el grupo"}


def test_schema_errors_keep_the_default_fastapi_format(client):
    response = client.post("/api/groups", json={"members": ["Ana", "Luis"]})

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)


def test_list_groups_with_member_count_and_total(client):
    group_id, ids = create_group(client)
    add_equal_expense(client, group_id, 3000, ids["Ana"], list(ids.values()))
    add_equal_expense(client, group_id, 1250, ids["Luis"], [ids["Luis"]])

    assert client.get("/api/groups").json() == [
        {"id": group_id, "name": "Piso Lavapiés", "currency": "EUR", "memberCount": 3, "totalSpentCents": 4250}
    ]


def test_add_member(client):
    group_id, _ = create_group(client)

    response = client.post(f"/api/groups/{group_id}/members", json={"name": "Javi"})

    assert response.status_code == 201
    assert response.json()["name"] == "Javi"
    assert len(client.get(f"/api/groups/{group_id}").json()["members"]) == 4


def test_member_names_are_unique_ignoring_case(client):
    group_id, _ = create_group(client)

    response = client.post(f"/api/groups/{group_id}/members", json={"name": "MARTA"})

    assert response.status_code == 422
    assert response.json() == {"detail": "Ya hay una persona llamada MARTA en el grupo"}


def test_unknown_group_returns_404(client):
    assert client.get("/api/groups/999").status_code == 404
    assert client.get("/api/groups/999").json() == {"detail": "Grupo no encontrado"}
    assert client.get("/api/groups/999/balances").status_code == 404
    assert client.post("/api/groups/999/members", json={"name": "Ana"}).status_code == 404


# ---------- Expenses ----------


def test_create_expense_with_equal_split(client):
    group_id, ids = create_group(client)

    expense = add_equal_expense(client, group_id, 8450, ids["Ana"], [ids["Ana"], ids["Luis"], ids["Marta"]])

    assert expense["description"] == "Cena"
    assert expense["amountCents"] == 8450
    assert expense["paidBy"] == ids["Ana"]
    assert expense["createdAt"].endswith("Z")
    assert [share["amountCents"] for share in expense["shares"]] == [2817, 2817, 2816]


def test_create_expense_with_exact_split(client):
    group_id, ids = create_group(client)

    response = client.post(
        f"/api/groups/{group_id}/expenses",
        json={
            "description": "Súper",
            "amountCents": 5000,
            "paidBy": ids["Luis"],
            "split": {
                "mode": "exact",
                "shares": [
                    {"memberId": ids["Ana"], "amountCents": 2000},
                    {"memberId": ids["Luis"], "amountCents": 3000},
                ],
            },
        },
    )

    assert response.status_code == 201
    assert response.json()["shares"] == [
        {"memberId": ids["Ana"], "amountCents": 2000},
        {"memberId": ids["Luis"], "amountCents": 3000},
    ]


def test_exact_split_must_match_the_total(client):
    group_id, ids = create_group(client)

    response = client.post(
        f"/api/groups/{group_id}/expenses",
        json={
            "description": "Súper",
            "amountCents": 5000,
            "paidBy": ids["Luis"],
            "split": {"mode": "exact", "shares": [{"memberId": ids["Ana"], "amountCents": 4000}]},
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "El reparto suma 40,00, pero el gasto es de 50,00"}


def test_expense_rejects_people_from_another_group(client):
    group_id, ids = create_group(client)
    _, other_ids = create_group(client, members=("Pablo", "Lucía"))

    payer_outside = client.post(
        f"/api/groups/{group_id}/expenses",
        json={"description": "Taxi", "amountCents": 1000, "paidBy": other_ids["Pablo"],
              "split": {"mode": "equal", "memberIds": [ids["Ana"]]}},
    )
    share_outside = client.post(
        f"/api/groups/{group_id}/expenses",
        json={"description": "Taxi", "amountCents": 1000, "paidBy": ids["Ana"],
              "split": {"mode": "equal", "memberIds": [ids["Ana"], other_ids["Lucía"]]}},
    )

    assert payer_outside.status_code == 422
    assert payer_outside.json() == {"detail": "La persona que paga no pertenece al grupo"}
    assert share_outside.status_code == 422
    assert share_outside.json() == {"detail": "Alguna persona del reparto no pertenece al grupo"}


def test_expense_amount_must_be_positive(client):
    group_id, ids = create_group(client)

    response = client.post(
        f"/api/groups/{group_id}/expenses",
        json={"description": "Nada", "amountCents": 0, "paidBy": ids["Ana"],
              "split": {"mode": "equal", "memberIds": [ids["Ana"]]}},
    )

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)


def test_delete_expense(client):
    group_id, ids = create_group(client)
    expense = add_equal_expense(client, group_id, 3000, ids["Ana"], list(ids.values()))

    response = client.delete(f"/api/groups/{group_id}/expenses/{expense['id']}")

    assert response.status_code == 204
    assert client.get(f"/api/groups/{group_id}").json()["expenses"] == []
    again = client.delete(f"/api/groups/{group_id}/expenses/{expense['id']}")
    assert again.status_code == 404
    assert again.json() == {"detail": "Gasto no encontrado"}


def test_cannot_delete_an_expense_through_another_group(client):
    group_id, ids = create_group(client)
    other_group_id, _ = create_group(client, members=("Pablo", "Lucía"))
    expense = add_equal_expense(client, group_id, 3000, ids["Ana"], list(ids.values()))

    response = client.delete(f"/api/groups/{other_group_id}/expenses/{expense['id']}")

    assert response.status_code == 404
    assert len(client.get(f"/api/groups/{group_id}").json()["expenses"]) == 1


def test_expenses_are_listed_newest_first(client):
    group_id, ids = create_group(client)
    first = add_equal_expense(client, group_id, 1000, ids["Ana"], [ids["Ana"]])
    second = add_equal_expense(client, group_id, 2000, ids["Ana"], [ids["Ana"]])

    expenses = client.get(f"/api/groups/{group_id}").json()["expenses"]

    assert [expense["id"] for expense in expenses] == [second["id"], first["id"]]


# ---------- Balances, settlements and payments ----------


def test_balances(client):
    group_id, ids = create_group(client)
    add_equal_expense(client, group_id, 9000, ids["Ana"], list(ids.values()))

    balances = client.get(f"/api/groups/{group_id}/balances").json()

    assert balances == [
        {"memberId": ids["Ana"], "name": "Ana", "paidCents": 9000, "owedCents": 3000, "netCents": 6000},
        {"memberId": ids["Luis"], "name": "Luis", "paidCents": 0, "owedCents": 3000, "netCents": -3000},
        {"memberId": ids["Marta"], "name": "Marta", "paidCents": 0, "owedCents": 3000, "netCents": -3000},
    ]


def test_settlements_shrink_after_a_payment(client):
    group_id, ids = create_group(client)
    add_equal_expense(client, group_id, 9000, ids["Ana"], list(ids.values()))

    settlements = client.get(f"/api/groups/{group_id}/settlements").json()
    assert settlements[0] == {
        "fromMemberId": ids["Luis"],
        "fromName": "Luis",
        "toMemberId": ids["Ana"],
        "toName": "Ana",
        "amountCents": 3000,
    }
    assert get_settlements(client, group_id) == [("Luis", "Ana", 3000), ("Marta", "Ana", 3000)]

    payment = post_payment(client, group_id, ids["Luis"], ids["Ana"], 3000)
    assert payment.status_code == 201
    assert payment.json()["amountCents"] == 3000
    assert payment.json()["createdAt"].endswith("Z")

    assert get_settlements(client, group_id) == [("Marta", "Ana", 3000)]
    assert len(client.get(f"/api/groups/{group_id}").json()["payments"]) == 1


def test_settled_group_has_no_settlements(client):
    group_id, ids = create_group(client, members=("Ana", "Luis"))
    add_equal_expense(client, group_id, 1000, ids["Ana"], list(ids.values()))
    post_payment(client, group_id, ids["Luis"], ids["Ana"], 500)

    assert get_settlements(client, group_id) == []


def test_payment_rules(client):
    group_id, ids = create_group(client)
    _, other_ids = create_group(client, members=("Pablo", "Lucía"))

    to_self = post_payment(client, group_id, ids["Ana"], ids["Ana"], 100)
    outsider = post_payment(client, group_id, ids["Ana"], other_ids["Pablo"], 100)
    zero = post_payment(client, group_id, ids["Ana"], ids["Luis"], 0)

    assert to_self.status_code == 422
    assert to_self.json() == {"detail": "Quien paga y quien recibe tienen que ser personas distintas"}
    assert outsider.status_code == 422
    assert outsider.json() == {"detail": "Las dos personas del pago tienen que pertenecer al grupo"}
    assert zero.status_code == 422
    assert isinstance(zero.json()["detail"], list)
