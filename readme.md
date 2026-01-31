# Price Collector Service

Backend-сервис для периодического сбора цен с биржи Deribit, хранения исторических данных в PostgreSQL и предоставления REST API для чтения этих данных.

Сервис построен на FastAPI и асинхронном стеке, использует Celery для фоновых задач и полностью разворачивается через Docker.

---

## Что делает сервис

- Периодически запрашивает цены BTC/USD и ETH/USD с Deribit
- Сохраняет каждое полученное значение в базу данных
- Хранит историю цен (данные не перезаписываются)
- Предоставляет API для получения:
  - всех цен по тикеру
  - последней цены
  - последней цены на заданный момент времени

---

## Технологии

- Python 3.14
- FastAPI
- SQLAlchemy (async)
- PostgreSQL
- Celery
- Redis
- Alembic
- pytest
- Docker / Docker Compose

---

## Архитектура в двух словах

- **Celery worker** по расписанию запрашивает цены с Deribit
- Полученные данные сохраняются в PostgreSQL
- **FastAPI** предоставляет REST API для чтения данных
- **Redis** используется Celery как broker и result backend

---

## API

Базовый префикс: `/api/v1`

### Получить все цены по тикеру
```
GET /prices/all?ticker={ticker}}
```

### Получить последнюю цену
```
GET /prices/last?ticker={ticker}}
```

### Получить последнюю цену на момент времени
```
GET /prices/lastAtTime?ticker={ticker}}&ts={unix_ts_ms}}
```

---

## Файлы конфигураций

Для локальной разработки и тестирования используются файлы окружения `.env` и `.env.test`.

Перед первым запуском необходимо создать их из примера и настроить:

```
cp .env.example .env
cp .env.example .env.test
```
.env — конфигурация для обычного запуска приложения

.env.test — конфигурация для запуска тестов

Для переключения между конфигурациями используется переменная окружения ENV_FILE

```
$env:ENV_FILE = ".env"
```
или
```
$env:ENV_FILE = ".env.test"
pytest
```
### Во время тестов схема базы данных будет полностью пересоздана!

---

## Запуск проекта (Docker)

### Требования
- Docker
- Docker Compose

### Запуск

Предварительно должен быть создан и настроен .env
```
docker compose up --build
```
API доступен по адресу: http://127.0.0.1:8000

Swagger UI: http://127.0.0.1:8000/docs

---

## Локальный запуск (предварительно должен быть запущен Redis)

Следует создать виртуальную среду и активировать её (Windows):
```
python -m venv .venv
.\.venv\Scripts\activate
```

Установить Poetry:
```
pip install --upgrade pip
pip install poetry
```

Установить зависимости:
```
poetry install
```

Запуск FastAPI:
```
python -m src.main
```

Запуск Celery Worker:
```
celery -A src.worker.celery_app:celery_app worker -l INFO -P solo
```

Запуск Celery Beat:
```
celery -A src.worker.celery_app:celery_app beat -l INFO
```
---

## Design Decisions

### Асинхронный стек

Используется async FastAPI и async SQLAlchemy, так как сервис в основном работает с I/O (HTTP и БД).

### Celery для фоновых задач
Сбор цен вынесен в отдельный worker, чтобы API не зависело от внешних сервисов и не блокировалось.

### Redis как брокер
Простое и надёжное решение для Celery, легко разворачивается в Docker.

### Хранение истории цен
Цены не обновляются, а добавляются как новые записи — это упрощает работу с историческими данными.

### Docker
Проект одинаково запускается в локальной среде и при деплое, без ручной настройки окружения.