from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.models import Account, TransactionType, Transaction, Investment, User
from app.schemas import AccountCreate, AccountUpdate, AccountResponse, PaginatedResponse
from app.core.deps import get_current_user


router = APIRouter()


@router.get("/", response_model=List[AccountResponse])
def get_accounts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    include_archived: bool = False,
    account_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение списка счетов"""
    
    query = db.query(Account).filter(Account.user_id == current_user.id)
    
    if not include_archived:
        query = query.filter(Account.is_archived == False)
    
    if account_type:
        query = query.filter(Account.account_type == account_type)
    
    accounts = query.order_by(Account.sort_order, Account.created_at).offset(skip).limit(limit).all()
    
    return accounts


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение счёта по ID"""
    
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return account


@router.post("/", response_model=AccountResponse)
def create_account(
    account_data: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Создание нового счёта"""
    
    # Получаем максимальный sort_order для сортировки
    max_order = db.query(Account).filter(
        Account.user_id == current_user.id
    ).count()
    
    account = Account(
        **account_data.model_dump(),
        user_id=current_user.id,
        sort_order=max_order
    )
    
    db.add(account)
    db.commit()
    db.refresh(account)
    
    return account


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: int,
    account_data: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обновление счёта"""
    
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    update_data = account_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)
    
    db.commit()
    db.refresh(account)
    
    return account


@router.delete("/{account_id}")
def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удаление счёта (архивирование)"""
    
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Мягкое удаление через архивирование
    account.is_archived = True
    db.commit()
    
    return {"message": "Account archived successfully"}


@router.post("/merge")
def merge_accounts(
    source_account_id: int,
    target_account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Объединение счетов
    
    Все операции и инвестиции переносятся с source на target.
    Source архивируется.
    """
    
    source = db.query(Account).filter(
        Account.id == source_account_id,
        Account.user_id == current_user.id
    ).first()
    
    target = db.query(Account).filter(
        Account.id == target_account_id,
        Account.user_id == current_user.id
    ).first()
    
    if not source or not target:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if source.account_type != target.account_type:
        raise HTTPException(
            status_code=400,
            detail="Cannot merge accounts of different types"
        )
    
    # Атомарная миграция операций
    from sqlalchemy import update
    
    # Обновить source_account_id в transactions
    db.execute(
        update(Transaction).
        where(Transaction.source_account_id == source.id).
        values(source_account_id=target.id)
    )
    
    # Обновить target_account_id в transactions
    db.execute(
        update(Transaction).
        where(Transaction.target_account_id == source.id).
        values(target_account_id=target.id)
    )
    
    # Обновить account_id в investments
    db.execute(
        update(Investment).
        where(Investment.account_id == source.id).
        values(account_id=target.id)
    )
    
    # Пересчитать балансы
    target.balance = target.balance + source.balance
    source.balance = 0
    
    source.is_archived = True
    db.commit()
    
    return {"message": "Accounts merged successfully"}


@router.put("/reorder")
def reorder_accounts(
    account_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Изменение порядка счетов (для drag&drop)"""
    
    for index, account_id in enumerate(account_ids):
        account = db.query(Account).filter(
            Account.id == account_id,
            Account.user_id == current_user.id
        ).first()
        
        if account:
            account.sort_order = index
    
    db.commit()
    
    return {"message": "Order updated successfully"}
