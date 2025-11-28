"""
Example 03: FastAPI with SQLAlchemy Async Database
Пример 03: FastAPI с асинхронной базой данных SQLAlchemy

This example demonstrates:
Этот пример демонстрирует:
- Async database connection setup / Настройка асинхронного подключения к БД
- Session management with dependency injection / Управление сессиями через DI
- SQLAlchemy 2.0 models with mapped_column / Модели SQLAlchemy 2.0 с mapped_column
- CRUD operations using db.execute / CRUD операции через db.execute
- Difference between Schema (Pydantic) and Model (SQLAlchemy) / Различие между Schema и Model

CRITICAL CONCEPTS / КЛЮЧЕВЫЕ КОНЦЕПЦИИ:
==============================================================================
1. Schema vs Model / Schema против Model:
   - Schema (Pydantic): For API validation and serialization / Для валидации API и сериализации
   - Model (SQLAlchemy): For database table representation / Для представления таблиц БД

2. SQLAlchemy 2.0 Changes / Изменения в SQLAlchemy 2.0:
   - OLD: Column(Integer) -> NEW: mapped_column(Integer) / mapped_column вместо Column
   - OLD: db.query(Model) -> NEW: db.execute(select(Model)) / execute вместо query
   - OLD: relationship() -> NEW: Mapped[List[...]] / Типизация relationship

3. Async Patterns / Асинхронные паттерны:
   - AsyncSession instead of Session / AsyncSession вместо Session
   - create_async_engine instead of create_engine / Асинхронный engine
   - await db.execute() for all queries / await для всех запросов
"""

from typing import AsyncGenerator, List, Optional
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import String, Integer, select, delete
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# ==============================================================================
# DATABASE SETUP / НАСТРОЙКА БАЗЫ ДАННЫХ
# ==============================================================================

# SQLite async connection string
# For production, use PostgreSQL: postgresql+asyncpg://user:password@localhost/dbname
BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = f"sqlite+aiosqlite:///{BASE_DIR}/test.db"

# Create async engine / Создание асинхронного движка
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Log all SQL queries / Логировать все SQL запросы
    future=True  # Use SQLAlchemy 2.0 style / Использовать стиль 2.0
)

# Create async session factory / Фабрика асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit / Не истекать объекты после commit
    autocommit=False,
    autoflush=False
)


# ==============================================================================
# SQLALCHEMY MODELS (Database Tables) / МОДЕЛИ SQLALCHEMY (Таблицы БД)
# ==============================================================================

class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models
    Базовый класс для всех моделей SQLAlchemy
    """
    pass


class User(Base):
    """
    SQLAlchemy Model - represents database table
    Модель SQLAlchemy - представляет таблицу в базе данных

    This is NOT a Pydantic model! It's a database model.
    Это НЕ Pydantic модель! Это модель базы данных.

    Key differences from Pydantic Schema:
    Ключевые отличия от Pydantic Schema:
    - Inherits from Base (DeclarativeBase) / Наследуется от Base
    - Uses mapped_column() for fields / Использует mapped_column для полей
    - Maps to actual database table / Соответствует реальной таблице БД
    - Used with db.execute(select(User)) / Используется с db.execute
    """
    __tablename__ = "users"

    # SQLAlchemy 2.0 style with Mapped and mapped_column
    # Стиль SQLAlchemy 2.0 с Mapped и mapped_column

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    age: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True  # Optional field / Необязательное поле
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, name={self.name}, email={self.email})>"


# ==============================================================================
# PYDANTIC SCHEMAS (API Validation) / PYDANTIC СХЕМЫ (Валидация API)
# ==============================================================================

class UserBase(BaseModel):
    """
    Base Pydantic Schema - shared fields
    Базовая Pydantic схема - общие поля

    This is a Pydantic model for API validation, NOT a database model!
    Это Pydantic модель для валидации API, НЕ модель базы данных!
    """
    name: str = Field(..., min_length=1, max_length=100, description="User name")
    email: str = Field(..., description="User email address")
    age: Optional[int] = Field(None, ge=0, le=150, description="User age")


class UserCreate(UserBase):
    """
    Schema for creating a user (input from API request)
    Схема для создания пользователя (входные данные из API запроса)

    Used in POST /users endpoint
    Используется в POST /users эндпоинте
    """
    pass


class UserUpdate(BaseModel):
    """
    Schema for updating a user (all fields optional)
    Схема для обновления пользователя (все поля необязательные)

    Used in PUT /users/{user_id} endpoint
    Используется в PUT /users/{user_id} эндпоинте
    """
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=150)


class UserResponse(UserBase):
    """
    Schema for returning user data (output to API response)
    Схема для возврата данных пользователя (вывод в API ответ)

    Includes database-generated fields like 'id'
    Включает сгенерированные БД поля, такие как 'id'

    Used in GET /users and GET /users/{user_id} endpoints
    Используется в GET /users и GET /users/{user_id} эндпоинтах
    """
    id: int

    # Configure Pydantic to work with SQLAlchemy models
    # Настроить Pydantic для работы с моделями SQLAlchemy
    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# DATABASE DEPENDENCY / ЗАВИСИМОСТЬ БАЗЫ ДАННЫХ
# ==============================================================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides database session
    Зависимость, предоставляющая сессию базы данных

    This is a FastAPI dependency that:
    Это FastAPI зависимость, которая:
    1. Creates a new async session / Создает новую асинхронную сессию
    2. Yields it to the endpoint / Передает её в эндпоинт
    3. Closes it after request completes / Закрывает после завершения запроса

    Usage in endpoints:
    Использование в эндпоинтах:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ==============================================================================
# LIFESPAN CONTEXT MANAGER / КОНТЕКСТ ЖИЗНЕННОГО ЦИКЛА
# ==============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    Контекст жизненного цикла для событий запуска и остановки

    Startup: Create database tables / Запуск: Создание таблиц БД
    Shutdown: Dispose engine / Остановка: Освобождение engine
    """
    # Startup / Запуск
    async with engine.begin() as conn:
        # Create all tables / Создать все таблицы
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Database tables created / Таблицы БД созданы")

    yield  # Application runs / Приложение работает

    # Shutdown / Остановка
    await engine.dispose()
    print("✅ Database connection closed / Соединение с БД закрыто")


# ==============================================================================
# FASTAPI APPLICATION / ПРИЛОЖЕНИЕ FASTAPI
# ==============================================================================

app = FastAPI(
    title="FastAPI SQLAlchemy Async Example",
    description="Example with async database operations using SQLAlchemy 2.0",
    version="1.0.0",
    lifespan=lifespan
)


# ==============================================================================
# CRUD ENDPOINTS / CRUD ЭНДПОИНТЫ
# ==============================================================================

@app.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Create a new user in the database"
)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    CREATE operation / Операция СОЗДАНИЯ

    Steps / Шаги:
    1. Check if email already exists / Проверить, существует ли email
    2. Create SQLAlchemy model instance / Создать экземпляр модели SQLAlchemy
    3. Add to session / Добавить в сессию
    4. Commit transaction / Зафиксировать транзакцию
    5. Refresh to get generated ID / Обновить для получения сгенерированного ID
    6. Return user / Вернуть пользователя
    """
    # Check if email exists / Проверка существования email
    # SQLAlchemy 2.0 style: use execute() with select()
    # Стиль 2.0: использовать execute() с select()
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email {user_data.email} already exists"
        )

    # Create new user model / Создание новой модели пользователя
    # Convert Pydantic schema to SQLAlchemy model
    # Преобразование Pydantic схемы в SQLAlchemy модель
    db_user = User(
        name=user_data.name,
        email=user_data.email,
        age=user_data.age
    )

    # Add to session / Добавить в сессию
    db.add(db_user)

    # Commit transaction / Зафиксировать транзакцию
    await db.commit()

    # Refresh to get auto-generated fields / Обновить для получения auto-generated полей
    await db.refresh(db_user)

    return db_user


@app.get(
    "/users",
    response_model=List[UserResponse],
    summary="Get all users",
    description="Retrieve all users from the database"
)
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> List[User]:
    """
    READ operation (list) / Операция ЧТЕНИЯ (список)

    SQLAlchemy 2.0 pattern:
    Паттерн SQLAlchemy 2.0:
    - OLD: db.query(User).offset(skip).limit(limit).all()
    - NEW: db.execute(select(User).offset(skip).limit(limit))
    """
    result = await db.execute(
        select(User)
        .offset(skip)
        .limit(limit)
    )

    # .scalars() returns scalar values (User objects)
    # .all() converts to list
    users = result.scalars().all()

    return list(users)


@app.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Retrieve a specific user by their ID"
)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    READ operation (single item) / Операция ЧТЕНИЯ (один элемент)

    SQLAlchemy 2.0 pattern:
    - OLD: db.query(User).filter(User.id == user_id).first()
    - NEW: db.execute(select(User).where(User.id == user_id))
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )

    # .scalar_one_or_none() returns single object or None
    # .scalar_one_or_none() возвращает один объект или None
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )

    return user


@app.put(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    description="Update an existing user's information"
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    UPDATE operation / Операция ОБНОВЛЕНИЯ

    Steps / Шаги:
    1. Get existing user / Получить существующего пользователя
    2. Update fields that are provided / Обновить предоставленные поля
    3. Commit transaction / Зафиксировать транзакцию
    4. Refresh and return / Обновить и вернуть
    """
    # Get user / Получить пользователя
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )

    # Update only provided fields / Обновить только предоставленные поля
    update_data = user_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return user


@app.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description="Delete a user from the database"
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    DELETE operation / Операция УДАЛЕНИЯ

    SQLAlchemy 2.0 pattern:
    - OLD: db.query(User).filter(User.id == user_id).delete()
    - NEW: db.execute(delete(User).where(User.id == user_id))
    """
    # Check if user exists / Проверить существование пользователя
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )

    # Delete user / Удалить пользователя
    await db.execute(
        delete(User).where(User.id == user_id)
    )

    await db.commit()


@app.get("/")
async def root():
    """
    Root endpoint with API information
    Корневой эндпоинт с информацией об API
    """
    return {
        "message": "FastAPI SQLAlchemy Async Example",
        "endpoints": {
            "create_user": "POST /users",
            "get_users": "GET /users?skip=0&limit=100",
            "get_user": "GET /users/{user_id}",
            "update_user": "PUT /users/{user_id}",
            "delete_user": "DELETE /users/{user_id}"
        },
        "docs": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "key_concepts": {
            "schema_vs_model": {
                "schema": "Pydantic models for API validation (UserCreate, UserResponse)",
                "model": "SQLAlchemy models for database tables (User)"
            },
            "sqlalchemy_2.0": {
                "old_query": "db.query(User).filter(...).all()",
                "new_execute": "db.execute(select(User).where(...)).scalars().all()"
            },
            "async_patterns": {
                "session": "AsyncSession from async_sessionmaker",
                "engine": "create_async_engine with aiosqlite/asyncpg",
                "dependency": "Depends(get_db) for session injection"
            }
        }
    }
