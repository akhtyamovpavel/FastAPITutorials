"""
Unit of Work Pattern / Паттерн Unit of Work

Manages database transactions and coordinates repositories.
Управляет транзакциями БД и координирует репозитории.

WHY UNIT OF WORK? / ЗАЧЕМ UNIT OF WORK?
1. Transaction Management / Управление транзакциями
   - Single commit/rollback point / Единая точка commit/rollback
   - Ensures data consistency / Обеспечивает консистентность данных

2. Repository Coordination / Координация репозиториев
   - Share session between repositories / Общая сессия между репозиториями
   - Atomic operations across entities / Атомарные операции над сущностями

3. Clean Architecture / Чистая архитектура
   - Service layer doesn't manage transactions / Слой сервисов не управляет транзакциями
   - Single responsibility principle / Принцип единственной ответственности

PATTERN / ПАТТЕРН:
    async with UnitOfWork() as uow:
        user = await uow.users.get_by_id(1)
        user.username = "new_name"
        await uow.commit()  # Commit all changes / Закоммитить все изменения
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session_maker
from repositories.user_repository import UserRepository


class UnitOfWork:
    """
    Unit of Work for managing database transactions
    Unit of Work для управления транзакциями БД

    Provides:
    - Automatic session management / Автоматическое управление сессией
    - Transaction commit/rollback / Commit/rollback транзакций
    - Repository access / Доступ к репозиториям
    """

    def __init__(self):
        """Initialize UoW without session / Инициализировать UoW без сессии"""
        self._session: Optional[AsyncSession] = None
        self._users: Optional[UserRepository] = None

    async def __aenter__(self):
        """
        Context manager entry / Вход в контекстный менеджер

        Creates session and initializes repositories.
        Создает сессию и инициализирует репозитории.
        """
        # Create new session / Создать новую сессию
        self._session = async_session_maker()

        # Initialize repositories with shared session
        # Инициализировать репозитории с общей сессией
        self._users = UserRepository(self._session)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit / Выход из контекстного менеджера

        Automatically rollback on exception, close session.
        Автоматически откатывает при исключении, закрывает сессию.

        Args:
            exc_type: Exception type / Тип исключения
            exc_val: Exception value / Значение исключения
            exc_tb: Exception traceback / Traceback исключения
        """
        if exc_type is not None:
            # Rollback on exception / Откатить при исключении
            await self.rollback()

        # Close session / Закрыть сессию
        await self._session.close()

    @property
    def users(self) -> UserRepository:
        """
        Access to User repository / Доступ к репозиторию User

        Returns:
            UserRepository instance / Экземпляр UserRepository
        """
        if self._users is None:
            raise RuntimeError("UnitOfWork not initialized. Use 'async with UnitOfWork()' / UnitOfWork не инициализирован")
        return self._users

    # You can add more repositories here
    # Здесь можно добавить больше репозиториев:
    # @property
    # def products(self) -> ProductRepository:
    #     return self._products

    async def commit(self) -> None:
        """
        Commit all changes / Закоммитить все изменения

        Saves all pending changes to database.
        Сохраняет все ожидающие изменения в БД.
        """
        if self._session is None:
            raise RuntimeError("UnitOfWork not initialized / UnitOfWork не инициализирован")

        await self._session.commit()

    async def rollback(self) -> None:
        """
        Rollback all changes / Откатить все изменения

        Discards all pending changes.
        Отменяет все ожидающие изменения.
        """
        if self._session is None:
            raise RuntimeError("UnitOfWork not initialized / UnitOfWork не инициализирован")

        await self._session.rollback()

    async def flush(self) -> None:
        """
        Flush changes without committing / Применить изменения без коммита

        Sends changes to database but doesn't commit transaction.
        Useful for getting auto-generated IDs.

        Отправляет изменения в БД, но не коммитит транзакцию.
        Полезно для получения автоматически сгенерированных ID.
        """
        if self._session is None:
            raise RuntimeError("UnitOfWork not initialized / UnitOfWork не инициализирован")

        await self._session.flush()


# Example usage in service layer / Пример использования в слое сервисов:
"""
async def transfer_data_between_users(user_id_from: int, user_id_to: int):
    '''
    Example showing atomic operation across multiple repositories
    Пример атомарной операции с несколькими репозиториями
    '''
    async with UnitOfWork() as uow:
        # Get both users / Получить обоих пользователей
        user_from = await uow.users.get_by_id(user_id_from)
        user_to = await uow.users.get_by_id(user_id_to)

        # Do some operations / Выполнить операции
        # ... modify users ...

        # Commit everything together or rollback on error
        # Закоммитить все вместе или откатить при ошибке
        await uow.commit()
"""
