"""Demo data so the app is not empty the first time it runs."""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Expense, ExpenseShare, Group, Member, Payment
from app.services.splitting import split_equally, split_exactly


def seed_demo_data(db: Session) -> None:
    """Creates the "Viaje a Asturias" group, only if the database has no groups yet."""
    if db.scalar(select(func.count(Group.id))) > 0:
        return

    group = Group(
        name="Viaje a Asturias",
        currency="EUR",
        created_at=_at(13, 20, 0),
        members=[Member(name=name) for name in ("Ana", "Luis", "Marta", "Javi")],
    )
    db.add(group)
    db.flush()  # assigns ids to the group and its members

    ana, luis, marta, javi = (member.id for member in group.members)
    everyone = [ana, luis, marta, javi]
    member_ids = set(everyone)

    def add_expense(
        description: str, cents: int, paid_by: int, shares: dict[int, int], when: datetime
    ) -> None:
        db.add(
            Expense(
                group_id=group.id,
                description=description,
                amount_cents=cents,
                paid_by_member_id=paid_by,
                created_at=when,
                shares=[ExpenseShare(member_id=m, amount_cents=c) for m, c in shares.items()],
            )
        )

    add_expense(
        "Gasolina Madrid - Cangas de Onís", 6240, paid_by=luis, when=_at(14, 7, 30),
        shares=split_equally(6240, everyone, member_ids),
    )
    add_expense(
        "Apartamento en Cangas de Onís (2 noches)", 21000, paid_by=ana, when=_at(14, 16, 0),
        shares=split_equally(21000, everyone, member_ids),
    )
    add_expense(
        "Supermercado", 4910, paid_by=marta, when=_at(14, 17, 15),
        shares=split_equally(4910, everyone, member_ids),
    )
    add_expense(
        "Sidrería en Gijón", 7650, paid_by=javi, when=_at(15, 20, 30),
        shares=split_exactly(7650, [(ana, 1800), (luis, 2250), (marta, 1650), (javi, 1950)], member_ids),
    )
    # Javi went back to Madrid earlier, so he was not at this dinner.
    add_expense(
        "Cena en Llanes", 8450, paid_by=luis, when=_at(16, 19, 45),
        shares=split_equally(8450, [ana, luis, marta], member_ids),
    )

    db.add(
        Payment(
            group_id=group.id,
            from_member_id=javi,
            to_member_id=luis,
            amount_cents=1500,
            created_at=_at(17, 9, 0),
        )
    )
    db.commit()


def _at(day: int, hour: int, minute: int) -> datetime:
    """A moment of the (fictional) trip, in August 2026, UTC."""
    return datetime(2026, 8, day, hour, minute, tzinfo=timezone.utc)
