"""How an expense is divided between members. All amounts are integer cents."""


class InvalidSplitError(ValueError):
    """The requested split breaks a business rule. The message is shown to the user."""


def split_equally(
    total_cents: int, member_ids: list[int], group_member_ids: set[int]
) -> dict[int, int]:
    """Divides the total in equal parts.

    Cents that cannot be divided go one by one to the first members in the given order,
    e.g. 1000 cents among 3 members gives 334, 333 and 333.
    """
    _check_members(member_ids, group_member_ids)
    base, remainder = divmod(total_cents, len(member_ids))
    return {
        member_id: base + 1 if position < remainder else base
        for position, member_id in enumerate(member_ids)
    }


def split_exactly(
    total_cents: int, shares: list[tuple[int, int]], group_member_ids: set[int]
) -> dict[int, int]:
    """Validates a split where the amount of each member is given as (member_id, cents) pairs."""
    _check_members([member_id for member_id, _ in shares], group_member_ids)
    if any(amount < 0 for _, amount in shares):
        raise InvalidSplitError("Los importes no pueden ser negativos")

    assigned = sum(amount for _, amount in shares)
    if assigned != total_cents:
        raise InvalidSplitError(
            f"El reparto suma {_format_cents(assigned)}, "
            f"pero el gasto es de {_format_cents(total_cents)}"
        )
    return dict(shares)


def _format_cents(cents: int) -> str:
    """1234 -> '12,34' (Spanish decimal comma, no currency symbol)."""
    return f"{cents // 100},{cents % 100:02d}"


def _check_members(member_ids: list[int], group_member_ids: set[int]) -> None:
    if not member_ids:
        raise InvalidSplitError("Elige al menos una persona para repartir el gasto")
    if len(set(member_ids)) != len(member_ids):
        raise InvalidSplitError("Hay personas repetidas en el reparto")
    if not set(member_ids) <= group_member_ids:
        raise InvalidSplitError("Alguna persona del reparto no pertenece al grupo")
