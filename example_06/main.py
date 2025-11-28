"""
FastAPI Application with Full DDD Architecture
FastAPI приложение с полной DDD архитектурой

This file ties all layers together and demonstrates the complete architecture.
Этот файл связывает все слои вместе и демонстрирует полную архитектуру.

ARCHITECTURE LAYERS / СЛОИ АРХИТЕКТУРЫ:
┌─────────────────────────────────────────┐
│         API Layer (Routers)             │  HTTP requests/responses
│         Слой API (Роутеры)              │  HTTP запросы/ответы
├─────────────────────────────────────────┤
│      Service Layer (Business Logic)     │  Business rules
│      Слой сервисов (Бизнес-логика)      │  Бизнес-правила
├─────────────────────────────────────────┤
│    Unit of Work (Transaction Mgmt)      │  Transaction control
│    Unit of Work (Управление транзакц.)  │  Контроль транзакций
├─────────────────────────────────────────┤
│   Repository Layer (Data Access)        │  Database queries
│   Слой репозиториев (Доступ к данным)   │  Запросы к БД
├─────────────────────────────────────────┤
│      Domain Layer (Entities)            │  Business objects
│      Доменный слой (Сущности)           │  Бизнес-объекты
├─────────────────────────────────────────┤
│         Database (SQLite)               │  Data storage
│         База данных (SQLite)            │  Хранение данных
└─────────────────────────────────────────┘

DATA FLOW EXAMPLE / ПРИМЕР ПОТОКА ДАННЫХ:
1. Request: POST /users {"username": "john", "email": "john@example.com"}
2. Router validates with Pydantic (UserCreate DTO)
3. Service applies business rules (check uniqueness)
4. Factory creates User entity from DTO
5. Repository saves to database
6. UnitOfWork commits transaction
7. Service returns UserInDB
8. Router converts to UserResponse
9. Response: 201 Created with user data

WHY THIS ARCHITECTURE? / ЗАЧЕМ ЭТА АРХИТЕКТУРА?
✅ Separation of Concerns / Разделение ответственности
✅ Testability / Тестируемость
✅ Maintainability / Поддерживаемость
✅ Scalability / Масштабируемость
✅ Flexibility / Гибкость
✅ Clean Code / Чистый код
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn

from database import init_db
from routers import users


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler / Обработчик жизненного цикла приложения

    Initializes database on startup and cleanup on shutdown.
    Инициализирует БД при запуске и очищает при завершении.
    """
    # Startup / Запуск
    print("🚀 Initializing database / Инициализация БД...")
    await init_db()
    print("✅ Database initialized / БД инициализирована")

    yield

    # Shutdown / Завершение
    print("👋 Shutting down / Завершение работы...")


# Create FastAPI application / Создать FastAPI приложение
app = FastAPI(
    title="DDD User Management API",
    description="""
    Complete Domain-Driven Design implementation with FastAPI.
    Полная реализация Domain-Driven Design с FastAPI.

    ## Features / Возможности:
    * **Full DDD architecture** / Полная DDD архитектура
    * **Repository pattern** / Паттерн репозиториев
    * **Service layer** / Слой сервисов
    * **Unit of Work** / Unit of Work
    * **Factory pattern** / Паттерн фабрики
    * **DTOs for data transfer** / DTO для передачи данных
    * **100% async code** / 100% асинхронный код
    * **SQLAlchemy 2.0** / SQLAlchemy 2.0

    ## Architecture Benefits / Преимущества архитектуры:
    * Clean separation of concerns / Чистое разделение ответственности
    * Easy to test / Легко тестировать
    * Easy to maintain / Легко поддерживать
    * Easy to extend / Легко расширять
    * Database-agnostic / Независимость от БД
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Include routers / Подключить роутеры
app.include_router(users.router)


@app.get(
    "/",
    summary="Root endpoint / Корневой эндпоинт",
    description="Get API information / Получить информацию об API"
)
async def root():
    """
    Root endpoint with architecture overview
    Корневой эндпоинт с обзором архитектуры
    """
    return {
        "message": "DDD User Management API / API управления пользователями с DDD",
        "architecture": {
            "layers": [
                "API Layer (Routers) / Слой API (Роутеры)",
                "Service Layer (Business Logic) / Слой сервисов (Бизнес-логика)",
                "Unit of Work (Transactions) / Unit of Work (Транзакции)",
                "Repository Layer (Data Access) / Слой репозиториев (Доступ к данным)",
                "Domain Layer (Entities) / Доменный слой (Сущности)",
                "Database (SQLite) / База данных (SQLite)"
            ],
            "patterns": [
                "Repository Pattern / Паттерн репозиториев",
                "Service Layer / Слой сервисов",
                "Unit of Work / Unit of Work",
                "Factory Pattern / Паттерн фабрики",
                "DTO Pattern / Паттерн DTO"
            ],
            "benefits": [
                "Separation of Concerns / Разделение ответственности",
                "Testability / Тестируемость",
                "Maintainability / Поддерживаемость",
                "Scalability / Масштабируемость",
                "Flexibility / Гибкость"
            ]
        },
        "endpoints": {
            "users": "/users",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get(
    "/health",
    summary="Health check / Проверка здоровья",
    description="Check if API is running / Проверить работу API"
)
async def health():
    """Health check endpoint / Эндпоинт проверки здоровья"""
    return {
        "status": "healthy / здоров",
        "database": "connected / подключена",
        "architecture": "DDD with async SQLAlchemy 2.0"
    }


if __name__ == "__main__":
    """
    Run application / Запустить приложение

    Usage / Использование:
        python main.py

    Then visit / Затем перейти на:
        http://localhost:8000/docs - Swagger UI
        http://localhost:8000/redoc - ReDoc
    """
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║        DDD User Management API with FastAPI                  ║
    ║        API управления пользователями с DDD                   ║
    ║                                                              ║
    ║  Architecture / Архитектура:                                 ║
    ║  ├─ API Layer (Routers) / Слой API                          ║
    ║  ├─ Service Layer / Слой сервисов                           ║
    ║  ├─ Unit of Work / Unit of Work                             ║
    ║  ├─ Repository Layer / Слой репозиториев                    ║
    ║  ├─ Domain Layer / Доменный слой                            ║
    ║  └─ Database / База данных                                  ║
    ║                                                              ║
    ║  Docs: http://localhost:8000/docs                            ║
    ║  ReDoc: http://localhost:8000/redoc                          ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
