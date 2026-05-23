# JoKeR_Finance Backend

Backend для системы учёта личных финансов на FastAPI.

## Установка

```bash
# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt

# Копирование .env
cp .env.example .env
# Отредактируйте .env с вашими настройками
```

## Запуск

### Локально

```bash
# Запуск PostgreSQL и Redis (Docker)
docker-compose up -d postgres redis

# Применение миграций (TODO: настроить Alembic)
# alembic upgrade head

# Запуск сервера
uvicorn app.main:app --reload
```

### Docker Compose

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f backend
```

## API Documentation

После запуска сервера документация доступна по адресу:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Структура

```
app/
├── api/            # API endpoints (v1, v2, ...)
├── core/           # Конфигурация, безопасность
├── db/             # БД сессии, базовые классы
├── models/         # SQLAlchemy модели
├── schemas/        # Pydantic схемы
├── services/       # Бизнес-логика
└── utils/          # Утилиты (шифрование, расчёты)
```

## Разработка

### Добавление нового endpoint

1. Создать файл в `app/api/v1/<module>.py`
2. Определить router и endpoints
3. Добавить router в `app/main.py`

### Модели данных

Все модели находятся в `app/models/__init__.py`. После изменения моделей:

```bash
# Создать миграцию
alembic revision --autogenerate -m "Description"

# Применить миграцию
alembic upgrade head
```

## Тесты

```bash
pytest
```
