from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any

from app.db.session import get_db
from app.core.security import hash_password, verify_password
from app.core.jwt import create_access_token, create_refresh_token, decode_token
from app.models import User, Profile, Settings
from app.schemas import UserCreate, UserLogin, Token, TokenRefresh


router = APIRouter()


@router.post("/register", response_model=dict)
def register(user_data: UserCreate, db: Session = Depends(get_db)) -> Any:
    """Регистрация нового пользователя"""
    
    # Проверка существования email
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Проверка существования username
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Создание пользователя
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Создание профиля
    profile = Profile(user_id=user.id)
    db.add(profile)
    
    # Создание настроек
    settings = Settings(user_id=user.id)
    db.add(settings)
    
    db.commit()
    
    return {"message": "User registered successfully", "user_id": user.id}


@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)) -> Any:
    """Вход пользователя"""
    
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Создание токенов
    access_token = create_access_token(data={"sub": str(user.id), "type": "access"})
    refresh_token = create_refresh_token(data={"sub": str(user.id), "type": "refresh"})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
def refresh_token(token_data: TokenRefresh, db: Session = Depends(get_db)) -> Any:
    """Обновление токена"""
    
    payload = decode_token(token_data.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Создание новых токенов
    access_token = create_access_token(data={"sub": str(user.id), "type": "access"})
    refresh_token = create_refresh_token(data={"sub": str(user.id), "type": "refresh"})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=dict)
def get_current_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)  # TODO: добавить dependency для JWT
) -> Any:
    """Получение текущего пользователя"""
    # TODO: реализовать dependency для получения пользователя из JWT
    return {"message": "Implement JWT dependency"}
