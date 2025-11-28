"""
Base Repository Pattern / Базовый паттерн репозитория

This layer provides abstraction over data access.
Этот слой предоставляет абстракцию над доступом к данным.

WHY REPOSITORY? / ЗАЧЕМ РЕПОЗИТОРИЙ?
1. Abstraction / Абстракция - Hide database implementation details
2. Testability / Тестируемость - Easy to mock for unit tests
3. Consistency / Согласованность - Unified data access interface
4. Flexibility / Гибкость - Easy to switch databases
5. Reusability / Переиспользуемость - Common CRUD operations in one place

SQLALCHEMY 2.0 PATTERNS / ПАТТЕРНЫ SQLALCHEMY 2.0:
- Use session.execute() instead of session.query()
- Use select() for queries instead of Query API
- Always use await for async operations
"""

from typing import TypeVar, Generic, Type, Optional, Sequence
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import Base

# Generic type for any SQLAlchemy model
# Универсальный тип для любой модели SQLAlchemy
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic repository for CRUD operations / Универсальный репозиторий для CRUD операций

    This class implements common database operations for any model.
    Этот класс реализует общие операции с БД для любой модели.

    Usage / Использование:
        user_repo = BaseRepository(User, session)
        user = await user_repo.get_by_id(1)
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """
        Initialize repository / Инициализировать репозиторий

        Args:
            model: SQLAlchemy model class / Класс модели SQLAlchemy
            session: Async database session / Асинхронная сессия БД
        """
        self.model = model
        self.session = session

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        Get entity by ID / Получить сущность по ID

        SQLAlchemy 2.0: Use session.execute() + select()
        SQLAlchemy 2.0: Используем session.execute() + select()

        Args:
            id: Entity ID / ID сущности

        Returns:
            Model instance or None / Экземпляр модели или None
        """
        stmt = select(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[ModelType]:
        """
        Get all entities with pagination / Получить все сущности с пагинацией

        Args:
            skip: Number of records to skip / Количество пропускаемых записей
            limit: Maximum records to return / Максимум возвращаемых записей

        Returns:
            List of model instances / Список экземпляров модели
        """
        stmt = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self) -> int:
        """
        Count total entities / Подсчитать все сущности

        Uses SQL COUNT() for efficiency.
        Использует SQL COUNT() для эффективности.

        Returns:
            Total count / Общее количество
        """
        stmt = select(func.count()).select_from(self.model)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def create(self, entity: ModelType) -> ModelType:
        """
        Create new entity / Создать новую сущность

        Note: Does not commit! Use UnitOfWork for transaction management.
        Примечание: Не делает commit! Используйте UnitOfWork для управления транзакциями.

        Args:
            entity: Model instance to create / Экземпляр модели для создания

        Returns:
            Created entity / Созданная сущность
        """
        self.session.add(entity)
        await self.session.flush()  # Get ID without committing / Получить ID без коммита
        await self.session.refresh(entity)  # Refresh to get defaults / Обновить для получения значений по умолчанию
        return entity

    async def update(self, id: int, **kwargs) -> Optional[ModelType]:
        """
        Update entity by ID / Обновить сущность по ID

        SQLAlchemy 2.0: Use update() statement for efficiency
        SQLAlchemy 2.0: Используем update() для эффективности

        Args:
            id: Entity ID / ID сущности
            **kwargs: Fields to update / Поля для обновления

        Returns:
            Updated entity or None / Обновленная сущность или None
        """
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**kwargs)
            .returning(self.model)  # Return updated row / Вернуть обновленную строку
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()

    async def delete(self, id: int) -> bool:
        """
        Delete entity by ID / Удалить сущность по ID

        Args:
            id: Entity ID / ID сущности

        Returns:
            True if deleted, False if not found / True если удалено, False если не найдено
        """
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0

    async def exists(self, id: int) -> bool:
        """
        Check if entity exists / Проверить существование сущности

        Args:
            id: Entity ID / ID сущности

        Returns:
            True if exists / True если существует
        """
        stmt = select(func.count()).select_from(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0
