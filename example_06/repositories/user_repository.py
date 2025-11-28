"""
User Repository / Репозиторий пользователей

Specialized repository for User entity with custom queries.
Специализированный репозиторий для сущности User с кастомными запросами.

WHY EXTEND BASE REPOSITORY? / ЗАЧЕМ РАСШИРЯТЬ БАЗОВЫЙ РЕПОЗИТОРИЙ?
- Add domain-specific queries / Добавить доменно-специфичные запросы
- Implement complex filtering / Реализовать сложную фильтрацию
- Encapsulate business query logic / Инкапсулировать логику бизнес-запросов
"""

from typing import Optional, Sequence
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models import User
from repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository for User entity / Репозиторий для сущности User

    Extends BaseRepository with User-specific queries.
    Расширяет BaseRepository пользовательскими запросами.
    """

    def __init__(self, session: AsyncSession):
        """Initialize with User model / Инициализировать с моделью User"""
        super().__init__(User, session)

    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Find user by username / Найти пользователя по имени

        Business rule: Username is unique identifier
        Бизнес-правило: Имя пользователя - уникальный идентификатор

        Args:
            username: Username to search / Имя пользователя для поиска

        Returns:
            User or None / Пользователь или None
        """
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Find user by email / Найти пользователя по email

        Business rule: Email is unique identifier
        Бизнес-правило: Email - уникальный идентификатор

        Args:
            email: Email to search / Email для поиска

        Returns:
            User or None / Пользователь или None
        """
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_users(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[User]:
        """
        Get only active users / Получить только активных пользователей

        Business filter: is_active = True
        Бизнес-фильтр: is_active = True

        Args:
            skip: Pagination offset / Смещение для пагинации
            limit: Maximum results / Максимум результатов

        Returns:
            List of active users / Список активных пользователей
        """
        stmt = (
            select(User)
            .where(User.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def search_users(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[User]:
        """
        Search users by username or email / Поиск пользователей по имени или email

        Complex query with OR conditions and LIKE operator.
        Сложный запрос с условиями OR и оператором LIKE.

        Args:
            search_term: Term to search / Термин для поиска
            skip: Pagination offset / Смещение для пагинации
            limit: Maximum results / Максимум результатов

        Returns:
            List of matching users / Список совпадающих пользователей
        """
        search_pattern = f"%{search_term}%"
        stmt = (
            select(User)
            .where(
                or_(
                    User.username.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.full_name.ilike(search_pattern)
                )
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def username_exists(self, username: str, exclude_id: Optional[int] = None) -> bool:
        """
        Check if username already exists / Проверить существование имени пользователя

        Used for validation before create/update.
        Используется для валидации перед созданием/обновлением.

        Args:
            username: Username to check / Имя пользователя для проверки
            exclude_id: ID to exclude from check (for updates) / ID для исключения (для обновлений)

        Returns:
            True if username exists / True если имя существует
        """
        stmt = select(User).where(User.username == username)
        if exclude_id:
            stmt = stmt.where(User.id != exclude_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def email_exists(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """
        Check if email already exists / Проверить существование email

        Args:
            email: Email to check / Email для проверки
            exclude_id: ID to exclude from check (for updates) / ID для исключения (для обновлений)

        Returns:
            True if email exists / True если email существует
        """
        stmt = select(User).where(User.email == email)
        if exclude_id:
            stmt = stmt.where(User.id != exclude_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
