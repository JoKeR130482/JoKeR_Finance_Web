from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.models import Category, TransactionType
from app.schemas import CategoryCreate, CategoryUpdate, CategoryResponse
from app.core.deps import get_current_user
from app.models import User


router = APIRouter()


@router.get("/", response_model=List[CategoryResponse])
def get_categories(
    type: Optional[str] = None,
    include_system: bool = True,
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение списка категорий"""
    
    query = db.query(Category).filter(
        (Category.user_id == current_user.id) | (Category.user_id == None)
    )
    
    if type:
        query = query.filter(Category.type == type)
    
    if not include_system:
        query = query.filter(Category.is_system == False)
    
    if parent_id is not None:
        if parent_id == -1:
            # Корневые категории
            query = query.filter(Category.parent_id == None)
        else:
            query = query.filter(Category.parent_id == parent_id)
    
    categories = query.order_by(Category.name).all()
    
    return categories


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение категории по ID"""
    
    category = db.query(Category).filter(
        Category.id == category_id,
        (Category.user_id == current_user.id) | (Category.user_id == None)
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return category


@router.post("/", response_model=CategoryResponse)
def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Создание новой категории"""
    
    # Проверка родительской категории если указана
    if category_data.parent_id:
        parent = db.query(Category).filter(
            Category.id == category_data.parent_id,
            (Category.user_id == current_user.id) | (Category.user_id == None)
        ).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent category not found")
    
    category = Category(
        **category_data.model_dump(),
        user_id=current_user.id,
        is_system=False
    )
    
    db.add(category)
    db.commit()
    db.refresh(category)
    
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обновление категории"""
    
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if category.is_system:
        raise HTTPException(status_code=403, detail="Cannot modify system categories")
    
    update_data = category_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
    
    db.commit()
    db.refresh(category)
    
    return category


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удаление категории"""
    
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if category.is_system:
        raise HTTPException(status_code=403, detail="Cannot delete system categories")
    
    # Проверка наличия операций с этой категорией
    from app.models import Transaction
    transactions_count = db.query(Transaction).filter(
        Transaction.category_id == category_id
    ).count()
    
    if transactions_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete category with {transactions_count} transactions"
        )
    
    # Удаление дочерних категорий
    child_categories = db.query(Category).filter(
        Category.parent_id == category_id,
        Category.user_id == current_user.id
    ).all()
    
    for child in child_categories:
        db.delete(child)
    
    db.delete(category)
    db.commit()
    
    return {"message": "Category deleted successfully"}
