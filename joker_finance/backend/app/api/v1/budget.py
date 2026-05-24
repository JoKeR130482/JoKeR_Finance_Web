from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.models import BudgetPlan, Category, Account
from app.schemas import BudgetPlanCreate, BudgetPlanUpdate, BudgetPlanResponse, BudgetCopyRequest
from app.core.deps import get_current_user
from app.models import User
from sqlalchemy import and_


router = APIRouter()


@router.get("/", response_model=List[BudgetPlanResponse])
def get_budget_plans(
    month: int,
    year: int,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение планов бюджета на месяц"""
    
    query = db.query(BudgetPlan).filter(
        BudgetPlan.user_id == current_user.id,
        BudgetPlan.month == month,
        BudgetPlan.year == year
    )
    
    if category_id:
        query = query.filter(BudgetPlan.category_id == category_id)
    
    plans = query.all()
    
    return plans


@router.post("/", response_model=BudgetPlanResponse)
def create_budget_plan(
    plan_data: BudgetPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Создание плана бюджета"""
    
    # Проверка категории
    category = db.query(Category).filter(
        Category.id == plan_data.category_id,
        (Category.user_id == current_user.id) | (Category.user_id == None)
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Проверка существования плана
    existing = db.query(BudgetPlan).filter(
        BudgetPlan.user_id == current_user.id,
        BudgetPlan.category_id == plan_data.category_id,
        BudgetPlan.month == plan_data.month,
        BudgetPlan.year == plan_data.year
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Budget plan already exists for this category and month"
        )
    
    plan = BudgetPlan(
        **plan_data.model_dump(),
        user_id=current_user.id,
        actual_amount=0.0
    )
    
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    return plan


@router.put("/{plan_id}", response_model=BudgetPlanResponse)
def update_budget_plan(
    plan_id: int,
    plan_data: BudgetPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обновление плана бюджета"""
    
    plan = db.query(BudgetPlan).filter(
        BudgetPlan.id == plan_id,
        BudgetPlan.user_id == current_user.id
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Budget plan not found")
    
    update_data = plan_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan, field, value)
    
    db.commit()
    db.refresh(plan)
    
    return plan


@router.post("/copy")
def copy_budget(
    copy_request: BudgetCopyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Копирование бюджета из одного месяца в другой"""
    
    # Получение исходных планов
    source_plans = db.query(BudgetPlan).filter(
        BudgetPlan.user_id == current_user.id,
        BudgetPlan.month == copy_request.source_month,
        BudgetPlan.year == copy_request.source_year
    ).all()
    
    if not source_plans:
        raise HTTPException(
            status_code=404,
            detail="No budget plans found for source month"
        )
    
    copied_count = 0
    
    for source_plan in source_plans:
        # Проверка существования плана в целевом месяце
        existing = db.query(BudgetPlan).filter(
            BudgetPlan.user_id == current_user.id,
            BudgetPlan.category_id == source_plan.category_id,
            BudgetPlan.month == copy_request.target_month,
            BudgetPlan.year == copy_request.target_year
        ).first()
        
        if existing:
            continue  # Пропускаем если уже существует
        
        # Определение суммы для копирования
        if copy_request.copy_mode == "plan":
            planned_amount = source_plan.planned_amount
        elif copy_request.copy_mode == "actual":
            planned_amount = source_plan.actual_amount
            
            # Применение условия если указано
            if copy_request.condition == "gt" and source_plan.actual_amount <= source_plan.planned_amount:
                continue
            elif copy_request.condition == "lt" and source_plan.actual_amount >= source_plan.planned_amount:
                continue
        elif copy_request.copy_mode == "adjusted":
            difference = source_plan.actual_amount - source_plan.planned_amount
            planned_amount = source_plan.planned_amount + difference
        else:
            planned_amount = source_plan.planned_amount
        
        # Создание нового плана
        new_plan = BudgetPlan(
            user_id=current_user.id,
            account_id=source_plan.account_id,
            category_id=source_plan.category_id,
            month=copy_request.target_month,
            year=copy_request.target_year,
            planned_amount=planned_amount,
            actual_amount=0.0,
            comment=source_plan.comment
        )
        
        db.add(new_plan)
        copied_count += 1
    
    db.commit()
    
    return {"message": f"Copied {copied_count} budget plans"}


@router.get("/stats/{month}/{year}")
def get_budget_stats(
    month: int,
    year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение статистики бюджета за месяц"""
    
    plans = db.query(BudgetPlan).filter(
        BudgetPlan.user_id == current_user.id,
        BudgetPlan.month == month,
        BudgetPlan.year == year
    ).all()
    
    total_planned = sum(p.planned_amount for p in plans)
    total_actual = sum(p.actual_amount for p in plans)
    
    over_budget = [p for p in plans if p.actual_amount > p.planned_amount]
    under_budget = [p for p in plans if p.actual_amount < p.planned_amount]
    
    return {
        "total_planned": total_planned,
        "total_actual": total_actual,
        "difference": total_planned - total_actual,
        "plans_count": len(plans),
        "over_budget_count": len(over_budget),
        "under_budget_count": len(under_budget),
        "completion_percentage": (total_actual / total_planned * 100) if total_planned > 0 else 0
    }
