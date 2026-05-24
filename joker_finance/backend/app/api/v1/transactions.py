from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.models import Transaction, TransactionType, Account, Category
from app.schemas import TransactionCreate, TransactionUpdate, TransactionResponse, PaginatedResponse
from app.core.deps import get_current_user
from app.models import User


router = APIRouter()


@router.get("/", response_model=List[TransactionResponse])
def get_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    account_id: Optional[int] = None,
    category_id: Optional[int] = None,
    transaction_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    is_reconciled: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение списка операций с фильтрацией"""
    
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    
    if account_id:
        query = query.filter(
            (Transaction.source_account_id == account_id) | 
            (Transaction.target_account_id == account_id)
        )
    
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    
    if is_reconciled is not None:
        query = query.filter(Transaction.is_reconciled == is_reconciled)
    
    if search:
        # Поиск по заметке (расшифрованной) или другим полям
        query = query.filter(Transaction.note.ilike(f"%{search}%"))
    
    transactions = query.order_by(Transaction.date.desc()).offset(skip).limit(limit).all()
    
    return transactions


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение операции по ID"""
    
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return transaction


@router.post("/", response_model=TransactionResponse)
def create_transaction(
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Создание новой операции"""
    
    # Проверка существования счетов
    if transaction_data.source_account_id:
        source_account = db.query(Account).filter(
            Account.id == transaction_data.source_account_id,
            Account.user_id == current_user.id
        ).first()
        if not source_account:
            raise HTTPException(status_code=404, detail="Source account not found")
    
    if transaction_data.target_account_id:
        target_account = db.query(Account).filter(
            Account.id == transaction_data.target_account_id,
            Account.user_id == current_user.id
        ).first()
        if not target_account:
            raise HTTPException(status_code=404, detail="Target account not found")
    
    # Проверка категории
    if transaction_data.category_id:
        category = db.query(Category).filter(
            Category.id == transaction_data.category_id
        ).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    
    transaction = Transaction(
        **transaction_data.model_dump(),
        user_id=current_user.id
    )
    
    db.add(transaction)
    
    # Обновление баланса счёта
    if transaction_data.transaction_type == TransactionType.INCOME:
        if transaction_data.target_account_id:
            target_account.balance += transaction_data.amount
    elif transaction_data.transaction_type == TransactionType.EXPENSE:
        if transaction_data.source_account_id:
            source_account.balance -= transaction_data.amount
    elif transaction_data.transaction_type == TransactionType.TRANSFER:
        if transaction_data.source_account_id:
            source_account.balance -= transaction_data.amount
        if transaction_data.target_account_id:
            target_account.balance += transaction_data.amount
    
    db.commit()
    db.refresh(transaction)
    
    return transaction


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обновление операции"""
    
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    update_data = transaction_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(transaction, field, value)
    
    db.commit()
    db.refresh(transaction)
    
    return transaction


@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удаление операции"""
    
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Обратное обновление баланса
    if transaction.transaction_type == TransactionType.INCOME:
        if transaction.target_account_id:
            target_account = db.query(Account).filter(Account.id == transaction.target_account_id).first()
            if target_account:
                target_account.balance -= transaction.amount
    elif transaction.transaction_type == TransactionType.EXPENSE:
        if transaction.source_account_id:
            source_account = db.query(Account).filter(Account.id == transaction.source_account_id).first()
            if source_account:
                source_account.balance += transaction.amount
    elif transaction.transaction_type == TransactionType.TRANSFER:
        if transaction.source_account_id:
            source_account = db.query(Account).filter(Account.id == transaction.source_account_id).first()
            if source_account:
                source_account.balance += transaction.amount
        if transaction.target_account_id:
            target_account = db.query(Account).filter(Account.id == transaction.target_account_id).first()
            if target_account:
                target_account.balance -= transaction.amount
    
    db.delete(transaction)
    db.commit()
    
    return {"message": "Transaction deleted successfully"}


@router.post("/bulk-delete")
def bulk_delete_transactions(
    transaction_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Групповое удаление операций"""
    
    transactions = db.query(Transaction).filter(
        Transaction.id.in_(transaction_ids),
        Transaction.user_id == current_user.id
    ).all()
    
    for transaction in transactions:
        # Обратное обновление баланса
        if transaction.transaction_type == TransactionType.INCOME:
            if transaction.target_account_id:
                target_account = db.query(Account).filter(Account.id == transaction.target_account_id).first()
                if target_account:
                    target_account.balance -= transaction.amount
        elif transaction.transaction_type == TransactionType.EXPENSE:
            if transaction.source_account_id:
                source_account = db.query(Account).filter(Account.id == transaction.source_account_id).first()
                if source_account:
                    source_account.balance += transaction.amount
        elif transaction.transaction_type == TransactionType.TRANSFER:
            if transaction.source_account_id:
                source_account = db.query(Account).filter(Account.id == transaction.source_account_id).first()
                if source_account:
                    source_account.balance += transaction.amount
            if transaction.target_account_id:
                target_account = db.query(Account).filter(Account.id == transaction.target_account_id).first()
                if target_account:
                    target_account.balance -= transaction.amount
        
        db.delete(transaction)
    
    db.commit()
    
    return {"message": f"{len(transactions)} transactions deleted successfully"}
