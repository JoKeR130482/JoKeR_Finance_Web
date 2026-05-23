from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # App
    APP_NAME: str = "JoKeR_Finance"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/joker_finance"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Encryption (AES-256-GCM)
    ENCRYPTION_KEY_SALT: str = "joker-finance-salt"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    
    # External APIs
    MOEX_API_URL: str = "https://iss.moex.com/iss"
    YAHOO_FINANCE_URL: str = "https://query1.finance.yahoo.com"
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Получить настройки (singleton)"""
    return Settings()
