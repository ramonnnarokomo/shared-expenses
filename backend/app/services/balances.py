from dataclasses import dataclass

from app.models import Group


@dataclass(frozen=True)
class MemberBalance:
    member_id: int
    name: str
    paid_cents: int
    owed_cents: int
    net_cents: int


def compute_balances(group: Group) -> list[MemberBalance]:
    """Balance of every member of the group.

    - paid: what the member paid for expenses.
    - owed: the sum of the member's shares in all expenses.
    - net: paid - owed + payments sent - payments received.
      Positive means the group owes them money; negative means they owe money.
    """
    paid = {member.id: 0 for member in group.members}
    owed = {member.id: 0 for member in group.members}
    payments_net = {member.id: 0 for member in group.members}

    for expense in group.expenses:
        paid[expense.paid_by_member_id] += expense.amount_cents
        for share in expense.shares:
            owed[share.member_id] += share.amount_cents

    for payment in group.payments:
        payments_net[payment.from_member_id] += payment.amount_cents
        payments_net[payment.to_member_id] -= payment.amount_cents

    return [
        MemberBalance(
            member_id=member.id,
            name=member.name,
            paid_cents=paid[member.id],
            owed_cents=owed[member.id],
            net_cents=paid[member.id] - owed[member.id] + payments_net[member.id],
        )
        for member in group.members
    ]
