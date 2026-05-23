# Celery tasks for JoKeR_Finance

from app.celery import celery_app
from app.core.config import get_settings
import httpx
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models import CurrencyRate


settings = get_settings()


@celery_app.task
def fetch_currency_rates(date: str = None):
    """
    Фоновая задача для загрузки курсов валют
    
    :param date: Дата в формате YYYY-MM-DD (по умолчанию вчера)
    """
    if not date:
        date = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    db = SessionLocal()
    try:
        # Загрузка с MOEX
        fetch_moex_rates.delay(date)
        
        # Загрузка криптовалют с CoinGecko
        fetch_crypto_rates.delay(date)
        
    finally:
        db.close()
    
    return {"status": "started", "date": date}


@celery_app.task
def fetch_moex_rates(date: str):
    """Загрузка курсов валют с MOEX"""
    try:
        url = f"{settings.MOEX_API_URL}/statistics/engines/stock/markets/currency/sittings/{date}.json"
        
        with httpx.Client() as client:
            response = client.get(url, timeout=10.0)
            response.raise_for_status()
            data = response.json()
        
        # Парсинг и сохранение курсов
        # TODO: Реализовать парсинг данных MOEX
        
        return {"status": "success", "source": "moex", "date": date}
    
    except Exception as e:
        return {"status": "error", "source": "moex", "error": str(e)}


@celery_app.task
def fetch_crypto_rates(date: str):
    """Загрузка курсов криптовалют с CoinGecko"""
    try:
        url = f"{settings.COINGECKO_URL}/exchange_rates"
        
        with httpx.Client() as client:
            response = client.get(url, timeout=10.0)
            response.raise_for_status()
            data = response.json()
        
        # Парсинг и сохранение курсов
        # TODO: Реализовать парсинг данных CoinGecko
        
        return {"status": "success", "source": "coingecko", "date": date}
    
    except Exception as e:
        return {"status": "error", "source": "coingecko", "error": str(e)}


@celery_app.task
def update_budget_actuals():
    """
    Обновление фактических сумм в бюджете
    
    Запускается ежедневно для пересчёта actual_amount
    на основе операций за текущий месяц
    """
    db = SessionLocal()
    try:
        # TODO: Реализовать обновление бюджетов
        pass
    finally:
        db.close()
    
    return {"status": "completed"}


@celery_app.task
def sync_investment_prices():
    """
    Синхронизация текущих цен инвестиций
    
    Загружает актуальные котировки акций, криптовалют
    """
    db = SessionLocal()
    try:
        # TODO: Реализовать синхронизацию цен
        pass
    finally:
        db.close()
    
    return {"status": "completed"}


@celery_app.task
def cleanup_old_data(days: int = 365):
    """
    Очистка старых данных
    
    :param days: Удалять данные старше N дней
    """
    # TODO: Реализовать очистку
    return {"status": "completed", "days": days}
