from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class AccountType(str, Enum):
    CASH = "cash"
    BANK = "bank"
    CARD = "card"
    INVESTMENT = "investment"
    CRYPTO = "crypto"
    DEPOSIT = "deposit"


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


# === Auth Schemas ===

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


# === Account Schemas ===

class AccountBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    account_type: AccountType
    currency: str = "RUB"
    icon_url: Optional[str] = None
    tags: List[str] = []


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    account_type: Optional[AccountType] = None
    currency: Optional[str] = None
    icon_url: Optional[str] = None
    balance: Optional[float] = None
    is_archived: Optional[bool] = None
    sort_order: Optional[int] = None
    tags: Optional[List[str]] = None


class AccountResponse(AccountBase):
    id: int
    user_id: int
    balance: float
    is_archived: bool
    sort_order: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# === Transaction Schemas ===

class TransactionBase(BaseModel):
    source_account_id: Optional[int] = None
    target_account_id: Optional[int] = None
    category_id: Optional[int] = None
    transaction_type: TransactionType
    amount: float = Field(..., gt=0)
    currency: str = "RUB"
    date: datetime
    note: Optional[str] = None
    flags: List[str] = []


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    source_account_id: Optional[int] = None
    target_account_id: Optional[int] = None
    category_id: Optional[int] = None
    amount: Optional[float] = None
    date: Optional[datetime] = None
    note: Optional[str] = None
    flags: Optional[List[str]] = None
    is_reconciled: Optional[bool] = None


class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    is_reconciled: bool
    reconciliation_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# === Category Schemas ===

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    parent_id: Optional[int] = None
    type: TransactionType
    color: str = "#000000"
    icon_url: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    color: Optional[str] = None
    icon_url: Optional[str] = None


class CategoryResponse(CategoryBase):
    id: int
    user_id: Optional[int] = None
    is_system: bool
    
    class Config:
        from_attributes = True


# === Budget Schemas ===

class BudgetPlanBase(BaseModel):
    account_id: Optional[int] = None
    category_id: int
    month: int = Field(..., ge=1, le=12)
    year: int
    planned_amount: float = Field(..., gt=0)
    comment: Optional[str] = None


class BudgetPlanCreate(BudgetPlanBase):
    pass


class BudgetPlanUpdate(BaseModel):
    planned_amount: Optional[float] = None
    actual_amount: Optional[float] = None
    comment: Optional[str] = None
    color_zone: Optional[str] = None


class BudgetPlanResponse(BudgetPlanBase):
    id: int
    user_id: int
    actual_amount: float
    color_zone: Optional[str] = None
    
    class Config:
        from_attributes = True


class BudgetCopyRequest(BaseModel):
    source_month: int
    source_year: int
    target_month: int
    target_year: int
    copy_mode: str = "plan"  # plan, actual, adjusted
    condition: Optional[str] = None  # gt, lt, always (для actual mode)


# === Investment Schemas ===

class InvestmentBase(BaseModel):
    account_id: Optional[int] = None
    asset_type: str
    ticker: Optional[str] = None
    name: str
    quantity: float = Field(..., gt=0)
    average_price: float = 0.0
    current_price: float = 0.0
    currency: str = "RUB"
    interest_rate: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class InvestmentCreate(InvestmentBase):
    pass


class InvestmentUpdate(BaseModel):
    quantity: Optional[float] = None
    current_price: Optional[float] = None
    interest_rate: Optional[float] = None
    end_date: Optional[datetime] = None


class InvestmentResponse(InvestmentBase):
    id: int
    user_id: int
    purchase_dates: List[dict] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# === Currency Rate Schemas ===

class CurrencyRateBase(BaseModel):
    base_currency: str
    target_currency: str
    rate: float
    date: datetime
    source: Optional[str] = None


class CurrencyRateResponse(CurrencyRateBase):
    id: int
    
    class Config:
        from_attributes = True


# === Reconciliation Schemas ===

class ReconciliationLogCreate(BaseModel):
    account_id: int
    reconciliation_date: datetime
    actual_balance: float
    comment: Optional[str] = None


class ReconciliationLogResponse(BaseModel):
    id: int
    user_id: int
    account_id: int
    reconciliation_date: datetime
    actual_balance: float
    recorded_balance: float
    difference: float
    comment: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# === Widget Schemas ===

class WidgetBase(BaseModel):
    name: str
    query: str
    position_x: int = 0
    position_y: int = 0
    width: int = 1
    height: int = 1
    config: dict = {}


class WidgetCreate(WidgetBase):
    pass


class WidgetUpdate(BaseModel):
    name: Optional[str] = None
    query: Optional[str] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    config: Optional[dict] = None


class WidgetResponse(WidgetBase):
    id: int
    user_id: int
    
    class Config:
        from_attributes = True


# === Pagination ===

class PaginationParams(BaseModel):
    page: int = 1
    size: int = 20
    sort_by: Optional[str] = None
    sort_order: str = "desc"


class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    size: int
    pages: int
