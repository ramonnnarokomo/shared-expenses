from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Expense, ExpenseShare, Group, Member, Payment
from app.schemas import (
    BalanceOut,
    EqualSplit,
    ExpenseCreate,
    ExpenseOut,
    GroupCreate,
    GroupDetail,
    GroupSummary,
    MemberCreate,
    MemberOut,
    PaymentCreate,
    PaymentOut,
    SettlementOut,
    ShareOut,
)
from app.services.balances import compute_balances
from app.services.settlement import settle_debts
from app.services.splitting import InvalidSplitError, split_equally, split_exactly

router = APIRouter(prefix="/api/groups", tags=["groups"])

DbSession = Annotated[Session, Depends(get_db)]


def get_group(group_id: int, db: DbSession) -> Group:
    """Dependency that loads the group from the path or answers 404."""
    group = db.get(Group, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grupo no encontrado")
    return group


GroupFromPath = Annotated[Group, Depends(get_group)]


def business_error(message: str) -> HTTPException:
    """422 with a plain Spanish message, for rules the request schema cannot check."""
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=message)


def to_expense_out(expense: Expense) -> ExpenseOut:
    return ExpenseOut(
        id=expense.id,
        description=expense.description,
        amount_cents=expense.amount_cents,
        paid_by=expense.paid_by_member_id,
        created_at=expense.created_at,
        shares=[ShareOut(member_id=s.member_id, amount_cents=s.amount_cents) for s in expense.shares],
    )


def to_group_detail(group: Group) -> GroupDetail:
    return GroupDetail(
        id=group.id,
        name=group.name,
        currency=group.currency,
        members=[MemberOut.model_validate(member) for member in group.members],
        expenses=[to_expense_out(expense) for expense in group.expenses],
        payments=[PaymentOut.model_validate(payment) for payment in group.payments],
    )


# ---------- Groups and members ----------


@router.get("", response_model=list[GroupSummary])
def list_groups(db: DbSession) -> list[GroupSummary]:
    query = (
        select(Group)
        .options(selectinload(Group.members), selectinload(Group.expenses))
        .order_by(Group.created_at.desc(), Group.id.desc())
    )
    return [
        GroupSummary(
            id=group.id,
            name=group.name,
            currency=group.currency,
            member_count=len(group.members),
            total_spent_cents=sum(expense.amount_cents for expense in group.expenses),
        )
        for group in db.scalars(query)
    ]


@router.post("", response_model=GroupDetail, status_code=status.HTTP_201_CREATED)
def create_group(body: GroupCreate, db: DbSession) -> GroupDetail:
    if len(body.members) < 2:
        raise business_error("Un grupo necesita al menos 2 personas")
    lowercase_names = [name.casefold() for name in body.members]
    if len(set(lowercase_names)) != len(lowercase_names):
        raise business_error("Hay nombres repetidos en el grupo")

    group = Group(
        name=body.name,
        currency=body.currency,
        members=[Member(name=name) for name in body.members],
    )
    db.add(group)
    db.commit()
    return to_group_detail(group)


@router.get("/{group_id}", response_model=GroupDetail)
def get_group_detail(group: GroupFromPath) -> GroupDetail:
    return to_group_detail(group)


@router.post("/{group_id}/members", response_model=MemberOut, status_code=status.HTTP_201_CREATED)
def add_member(body: MemberCreate, group: GroupFromPath, db: DbSession) -> Member:
    if any(member.name.casefold() == body.name.casefold() for member in group.members):
        raise business_error(f"Ya hay una persona llamada {body.name} en el grupo")

    member = Member(name=body.name)
    group.members.append(member)
    db.commit()
    return member


# ---------- Expenses ----------


@router.post("/{group_id}/expenses", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(body: ExpenseCreate, group: GroupFromPath, db: DbSession) -> ExpenseOut:
    group_member_ids = {member.id for member in group.members}
    if body.paid_by not in group_member_ids:
        raise business_error("La persona que paga no pertenece al grupo")

    try:
        if isinstance(body.split, EqualSplit):
            shares = split_equally(body.amount_cents, body.split.member_ids, group_member_ids)
        else:
            pairs = [(share.member_id, share.amount_cents) for share in body.split.shares]
            shares = split_exactly(body.amount_cents, pairs, group_member_ids)
    except InvalidSplitError as error:
        raise business_error(str(error)) from error

    expense = Expense(
        group_id=group.id,
        description=body.description,
        amount_cents=body.amount_cents,
        paid_by_member_id=body.paid_by,
        shares=[ExpenseShare(member_id=m, amount_cents=cents) for m, cents in shares.items()],
    )
    db.add(expense)
    db.commit()
    return to_expense_out(expense)


@router.delete("/{group_id}/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, group: GroupFromPath, db: DbSession) -> None:
    expense = db.get(Expense, expense_id)
    if expense is None or expense.group_id != group.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gasto no encontrado")

    db.delete(expense)
    db.commit()


# ---------- Payments, balances and settlements ----------


@router.post("/{group_id}/payments", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def create_payment(body: PaymentCreate, group: GroupFromPath, db: DbSession) -> Payment:
    group_member_ids = {member.id for member in group.members}
    if body.from_member_id == body.to_member_id:
        raise business_error("Quien paga y quien recibe tienen que ser personas distintas")
    if not {body.from_member_id, body.to_member_id} <= group_member_ids:
        raise business_error("Las dos personas del pago tienen que pertenecer al grupo")

    payment = Payment(
        group_id=group.id,
        from_member_id=body.from_member_id,
        to_member_id=body.to_member_id,
        amount_cents=body.amount_cents,
    )
    db.add(payment)
    db.commit()
    return payment


@router.get("/{group_id}/balances", response_model=list[BalanceOut])
def get_balances(group: GroupFromPath) -> list[BalanceOut]:
    return [BalanceOut.model_validate(balance) for balance in compute_balances(group)]


@router.get("/{group_id}/settlements", response_model=list[SettlementOut])
def get_settlements(group: GroupFromPath) -> list[SettlementOut]:
    balances = compute_balances(group)
    names = {balance.member_id: balance.name for balance in balances}
    transfers = settle_debts({balance.member_id: balance.net_cents for balance in balances})
    return [
        SettlementOut(
            from_member_id=transfer.from_member_id,
            from_name=names[transfer.from_member_id],
            to_member_id=transfer.to_member_id,
            to_name=names[transfer.to_member_id],
            amount_cents=transfer.amount_cents,
        )
        for transfer in transfers
    ]
