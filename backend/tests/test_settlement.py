import random

import pytest

from app.services.settlement import Transfer, settle_debts


def test_one_debtor_one_creditor():
    assert settle_debts({1: 500, 2: -500}) == [
        Transfer(from_member_id=2, to_member_id=1, amount_cents=500)
    ]


def test_one_creditor_several_debtors():
    assert settle_debts({1: 900, 2: -400, 3: -500}) == [
        Transfer(3, 1, 500),
        Transfer(2, 1, 400),
    ]


def test_several_creditors_and_debtors():
    # Largest debtor (4) pays largest creditor (1) first, and so on.
    assert settle_debts({1: 1000, 2: 500, 3: -700, 4: -800}) == [
        Transfer(4, 1, 800),
        Transfer(3, 2, 500),
        Transfer(3, 1, 200),
    ]


def test_ties_are_broken_by_lowest_member_id():
    assert settle_debts({1: 300, 2: 300, 3: -300, 4: -300}) == [
        Transfer(3, 1, 300),
        Transfer(4, 2, 300),
    ]


def test_already_settled_group_needs_no_transfers():
    assert settle_debts({1: 0, 2: 0, 3: 0}) == []
    assert settle_debts({}) == []


def test_balances_must_add_up_to_zero():
    with pytest.raises(ValueError):
        settle_debts({1: 100, 2: -50})


@pytest.mark.parametrize("seed", range(20))
def test_transfers_settle_random_balances(seed):
    rng = random.Random(seed)
    member_count = rng.randint(2, 8)
    balances = {member_id: rng.randint(-20_000, 20_000) for member_id in range(1, member_count)}
    balances[member_count] = -sum(balances.values())  # make everything add up to zero

    transfers = settle_debts(balances)

    remaining = dict(balances)
    for transfer in transfers:
        assert transfer.amount_cents > 0
        remaining[transfer.from_member_id] += transfer.amount_cents
        remaining[transfer.to_member_id] -= transfer.amount_cents
    assert all(net == 0 for net in remaining.values())
    assert len(transfers) <= member_count - 1
