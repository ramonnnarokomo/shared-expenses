from dataclasses import dataclass


@dataclass(frozen=True)
class Transfer:
    from_member_id: int
    to_member_id: int
    amount_cents: int


def settle_debts(net_balances: dict[int, int]) -> list[Transfer]:
    """Returns the transfers that bring every balance to zero.

    `net_balances` maps member id -> net cents (positive: the group owes them;
    negative: they owe the group). The balances must add up to zero.

    Greedy algorithm: the member who owes the most pays the member who is owed the most,
    as much as possible (the smaller of both amounts). Every transfer leaves at least one
    of the two at zero, so n members need at most n - 1 transfers. It does not always find
    the absolute minimum number of transfers (that problem is NP-hard), but it is simple
    and works well for groups of friends. Ties are broken by the lowest member id so the
    result is always the same for the same input.
    """
    if sum(net_balances.values()) != 0:
        raise ValueError("Net balances must add up to zero")

    debts = {member_id: -net for member_id, net in net_balances.items() if net < 0}
    credits = {member_id: net for member_id, net in net_balances.items() if net > 0}

    transfers: list[Transfer] = []
    while debts:
        debtor = _largest(debts)
        creditor = _largest(credits)
        amount = min(debts[debtor], credits[creditor])
        transfers.append(Transfer(debtor, creditor, amount))

        debts[debtor] -= amount
        credits[creditor] -= amount
        if debts[debtor] == 0:
            del debts[debtor]
        if credits[creditor] == 0:
            del credits[creditor]

    return transfers


def _largest(amounts: dict[int, int]) -> int:
    """Member id with the largest amount; on a tie, the lowest id."""
    return max(amounts, key=lambda member_id: (amounts[member_id], -member_id))
