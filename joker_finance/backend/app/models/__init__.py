from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.session import Base


class AccountType(enum.Enum):
    CASH = "cash"
    BANK = "bank"
    CARD = "card"
    INVESTMENT = "investment"
    CRYPTO = "crypto"
    DEPOSIT = "deposit"


class TransactionType(enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


class User(Base):
    """Пользователь"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    profile = relationship("Profile", back_populates="user", uselist=False)
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("Settings", back_populates="user", uselist=False)


class Profile(Base):
    """Профиль пользователя"""
    __tablename__ = "profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    avatar_url = Column(String(500))
    timezone = Column(String(50), default="UTC")
    currency = Column(String(3), default="RUB")
    
    user = relationship("User", back_populates="profile")


class Settings(Base):
    """Настройки пользователя"""
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    theme = Column(String(20), default="system")  # light, dark, system
    language = Column(String(5), default="ru")
    encryption_key_salt = Column(String(255))
    
    user = relationship("User", back_populates="settings")


class Account(Base):
    """Счёт"""
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    account_type = Column(SQLEnum(AccountType), nullable=False)
    currency = Column(String(3), default="RUB")
    icon_url = Column(String(500))
    balance = Column(Float, default=0.0)
    is_archived = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="accounts")
    transactions_source = relationship("Transaction", foreign_keys="Transaction.source_account_id", back_populates="source_account")
    transactions_target = relationship("Transaction", foreign_keys="Transaction.target_account_id", back_populates="target_account")
    budget_plans = relationship("BudgetPlan", back_populates="account", cascade="all, delete-orphan")
    investments = relationship("Investment", back_populates="account", cascade="all, delete-orphan")


class Category(Base):
    """Категория операций"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # NULL = системная
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id"))
    type = Column(SQLEnum(TransactionType), nullable=False)
    color = Column(String(7), default="#000000")
    icon_url = Column(String(500))
    is_system = Column(Boolean, default=False)
    
    parent = relationship("Category", remote_side=[id], backref="children")
    transactions = relationship("Transaction", back_populates="category")


class Transaction(Base):
    """Операция"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    source_account_id = Column(Integer, ForeignKey("accounts.id"))
    target_account_id = Column(Integer, ForeignKey("accounts.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="RUB")
    date = Column(DateTime(timezone=True), nullable=False)
    note = Column(Text)  # Шифруется
    flags = Column(JSON, default=list)
    is_reconciled = Column(Boolean, default=False)
    reconciliation_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    source_account = relationship("Account", foreign_keys=[source_account_id], back_populates="transactions_source")
    target_account = relationship("Account", foreign_keys=[target_account_id], back_populates="transactions_target")
    category = relationship("Category", back_populates="transactions")


class BudgetPlan(Base):
    """План бюджета"""
    __tablename__ = "budget_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))
    month = Column(Integer, nullable=False)  # 1-12
    year = Column(Integer, nullable=False)
    planned_amount = Column(Float, nullable=False)
    actual_amount = Column(Float, default=0.0)
    comment = Column(Text)
    color_zone = Column(String(20))  # green, yellow, orange, red
    
    account = relationship("Account", back_populates="budget_plans")
    category = relationship("Category")


class Investment(Base):
    """Инвестиция (акции, крипта, депозиты)"""
    __tablename__ = "investments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    asset_type = Column(String(50), nullable=False)  # stock, crypto, deposit, bond, etf
    ticker = Column(String(50))
    name = Column(String(200), nullable=False)
    quantity = Column(Float, nullable=False)
    average_price = Column(Float, default=0.0)
    current_price = Column(Float, default=0.0)
    currency = Column(String(3), default="RUB")
    interest_rate = Column(Float)  # Для депозитов
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    purchase_dates = Column(JSON, default=list)  # FIFO: [{date, quantity, price}, ...]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    account = relationship("Account", back_populates="investments")


class CurrencyRate(Base):
    """Курсы валют"""
    __tablename__ = "currency_rates"
    
    id = Column(Integer, primary_key=True, index=True)
    base_currency = Column(String(3), nullable=False)
    target_currency = Column(String(3), nullable=False)
    rate = Column(Float, nullable=False)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    source = Column(String(50))  # moex, yfinance, coingecko
    
    __table_args__ = (
        # Уникальность пары + дата
        {'sqlite_autoincrement': True}
    )


class ReconciliationLog(Base):
    """История сверок"""
    __tablename__ = "reconciliation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    reconciliation_date = Column(DateTime(timezone=True), nullable=False)
    actual_balance = Column(Float, nullable=False)
    recorded_balance = Column(Float, nullable=False)
    difference = Column(Float)
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    account = relationship("Account")


class Widget(Base):
    """Пользовательский виджет"""
    __tablename__ = "widgets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    query = Column(Text, nullable=False)  # SQL/DSL правило
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)
    width = Column(Integer, default=1)
    height = Column(Integer, default=1)
    config = Column(JSON, default=dict)
    
    user = relationship("User")
