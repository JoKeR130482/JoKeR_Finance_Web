# JoKeR_Finance Web

Веб-приложение для учёта личных финансов и инвестиций (аналог Family 13 Premium).

## Структура проекта

```
joker_finance/
├── backend/                 # Python/FastAPI бэкенд
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Конфигурация, безопасность
│   │   ├── db/             # БД сессии, базовые классы
│   │   ├── models/         # SQLAlchemy модели
│   │   ├── schemas/        # Pydantic схемы
│   │   ├── services/       # Бизнес-логика
│   │   └── utils/          # Утилиты (шифрование, расчёты)
│   └── tests/              # Тесты
├── frontend/               # React/Vue фронтенд
├── docs/                   # Документация
└── scripts/                # Скрипты развёртывания
```

## Технологический стек

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy + Alembic
- PostgreSQL 15+
- Redis
- Celery
- cryptography (AES-256-GCM)

### Frontend
- React/Vue 3
- Next.js/Nuxt
- TailwindCSS
- Zustand/Pinia

## Быстрый старт

### Требования
- Python 3.11+
- PostgreSQL 15+
- Redis
- Node.js 18+

### Установка бэкенда

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### Установка фронтенда

```bash
cd frontend
npm install
```

### Запуск

```bash
# Бэкенд
cd backend
uvicorn app.main:app --reload

# Фронтенд
cd frontend
npm run dev
```

## Лицензия

MIT
