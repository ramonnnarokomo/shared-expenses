from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from app.db import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UtcDateTime(TypeDecorator):
    """Stores datetimes in UTC and always returns them timezone-aware.

    SQLite has no real datetime type and drops the timezone, so we store naive UTC
    values and attach UTC again when reading them back.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc)


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utc_now)

    members: Mapped[list["Member"]] = relationship(
        back_populates="group", cascade="all, delete-orphan", order_by="Member.id"
    )
    # Newest first, which is how the API returns them.
    expenses: Mapped[list["Expense"]] = relationship(
        cascade="all, delete-orphan",
        order_by="[Expense.created_at.desc(), Expense.id.desc()]",
    )
    payments: Mapped[list["Payment"]] = relationship(
        cascade="all, delete-orphan",
        order_by="[Payment.created_at.desc(), Payment.id.desc()]",
    )


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    name: Mapped[str] = mapped_column(String(50))

    group: Mapped[Group] = relationship(back_populates="members")


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    description: Mapped[str] = mapped_column(String(120))
    amount_cents: Mapped[int]
    paid_by_member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utc_now)

    # "selectin" loads the shares of all expenses in one extra query instead of one per expense.
    shares: Mapped[list["ExpenseShare"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin", order_by="ExpenseShare.member_id"
    )


class ExpenseShare(Base):
    """The part of an expense that one member has to pay."""

    __tablename__ = "expense_shares"

    expense_id: Mapped[int] = mapped_column(ForeignKey("expenses.id"), primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), primary_key=True)
    amount_cents: Mapped[int]


class Payment(Base):
    """Money sent from one member to another to settle debts."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    from_member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    to_member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    amount_cents: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utc_now)
