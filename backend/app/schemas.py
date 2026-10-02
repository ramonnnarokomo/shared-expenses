"""Request and response bodies of the API.

Python code uses snake_case; the JSON uses camelCase thanks to the alias generator.
"""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from pydantic.alias_generators import to_camel

# Upper limit for any amount (1.000.000,00), so absurd values never reach the database.
MAX_CENTS = 100_000_000

PositiveCents = Annotated[int, Field(gt=0, le=MAX_CENTS)]
NonNegativeCents = Annotated[int, Field(ge=0, le=MAX_CENTS)]
MemberName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


# ---------- Groups and members ----------


class GroupCreate(CamelModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    currency: Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")] = "EUR"
    members: list[MemberName]


class MemberCreate(CamelModel):
    name: MemberName


class MemberOut(CamelModel):
    id: int
    name: str


class GroupSummary(CamelModel):
    id: int
    name: str
    currency: str
    member_count: int
    total_spent_cents: int


# ---------- Expenses ----------


class EqualSplit(CamelModel):
    mode: Literal["equal"]
    member_ids: list[int]


class ExactShareIn(CamelModel):
    member_id: int
    amount_cents: NonNegativeCents


class ExactSplit(CamelModel):
    mode: Literal["exact"]
    shares: list[ExactShareIn]


# Pydantic picks the right model by looking at the "mode" field.
Split = Annotated[EqualSplit | ExactSplit, Field(discriminator="mode")]


class ExpenseCreate(CamelModel):
    description: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    amount_cents: PositiveCents
    paid_by: int
    split: Split


class ShareOut(CamelModel):
    member_id: int
    amount_cents: int


class ExpenseOut(CamelModel):
    id: int
    description: str
    amount_cents: int
    paid_by: int
    created_at: datetime
    shares: list[ShareOut]


# ---------- Payments, balances and settlements ----------


class PaymentCreate(CamelModel):
    from_member_id: int
    to_member_id: int
    amount_cents: PositiveCents


class PaymentOut(CamelModel):
    id: int
    from_member_id: int
    to_member_id: int
    amount_cents: int
    created_at: datetime


class GroupDetail(CamelModel):
    id: int
    name: str
    currency: str
    members: list[MemberOut]
    expenses: list[ExpenseOut]
    payments: list[PaymentOut]


class BalanceOut(CamelModel):
    member_id: int
    name: str
    paid_cents: int
    owed_cents: int
    net_cents: int


class SettlementOut(CamelModel):
    from_member_id: int
    from_name: str
    to_member_id: int
    to_name: str
    amount_cents: int
