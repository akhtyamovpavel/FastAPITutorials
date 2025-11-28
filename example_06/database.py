"""
Database Configuration / Конфигурация базы данных

This module sets up SQLAlchemy 2.0 async engine and session factory.
Этот модуль настраивает асинхронный движок SQLAlchemy 2.0 и фабрику сессий.

Why async? / Почему async?
- Non-blocking database operations / Неблокирующие операции с БД
- Better performance under load / Лучшая производительность под нагрузкой
- FastAPI is async-first framework / FastAPI - асинхронный фреймворк
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# SQLAlchemy 2.0: Use async engine for async operations
# SQLAlchemy 2.0: Используем async engine для асинхронных операций
DATABASE_URL = "sqlite+aiosqlite:///./example_06.db"

# Create async engine with echo for SQL debugging
# Создаем async engine с echo для отладки SQL
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Print SQL queries / Печатать SQL запросы
    future=True  # Use SQLAlchemy 2.0 API / Использовать API SQLAlchemy 2.0
)

# Session factory for creating database sessions
# Фабрика сессий для создания сессий базы данных
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keep objects usable after commit / Сохранять объекты после коммита
    autoflush=False,  # Manual control over flushing / Ручной контроль над flush
    autocommit=False  # Explicit transaction control / Явный контроль транзакций
)


# Base class for all ORM models / Базовый класс для всех ORM моделей
class Base(DeclarativeBase):
    """
    Declarative base for SQLAlchemy 2.0
    Декларативная база для SQLAlchemy 2.0

    All domain models inherit from this class.
    Все доменные модели наследуются от этого класса.
    """
    pass


async def get_session() -> AsyncSession:
    """
    Dependency for getting database session / Зависимость для получения сессии БД

    Usage in FastAPI / Использование в FastAPI:
        @app.get("/users")
        async def get_users(session: AsyncSession = Depends(get_session)):
            ...

    Yields:
        AsyncSession: Database session / Сессия базы данных
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """
    Initialize database tables / Инициализация таблиц базы данных

    Creates all tables defined in Base.metadata
    Создает все таблицы, определенные в Base.metadata
    """
    async with engine.begin() as conn:
        # Drop all tables (for development only!)
        # Удалить все таблицы (только для разработки!)
        await conn.run_sync(Base.metadata.drop_all)

        # Create all tables / Создать все таблицы
        await conn.run_sync(Base.metadata.create_all)
