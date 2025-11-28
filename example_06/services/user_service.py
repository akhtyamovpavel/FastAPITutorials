"""
Service Layer / Слой сервисов

Contains business logic and orchestrates repositories.
Содержит бизнес-логику и оркеструет репозитории.

WHY SERVICE LAYER? / ЗАЧЕМ СЛОЙ СЕРВИСОВ?
1. Business Logic / Бизнес-логика
   - Encapsulate complex business rules / Инкапсулировать сложные бизнес-правила
   - Coordinate multiple repositories / Координировать несколько репозиториев
   - Validate business constraints / Валидировать бизнес-ограничения

2. Separation of Concerns / Разделение ответственности
   - Keep routers thin / Держать роутеры тонкими
   - Keep repositories focused on data access / Держать репозитории сфокусированными на доступе к данным
   - Business logic in one place / Бизнес-логика в одном месте

3. Testability / Тестируемость
   - Test business logic without HTTP layer / Тестировать логику без HTTP слоя
   - Easy to mock repositories / Легко мокировать репозитории

4. Reusability / Переиспользуемость
   - Use same logic in different contexts / Использовать ту же логику в разных контекстах
   - CLI, API, background jobs all use services / CLI, API, фоновые задачи используют сервисы

DATA FLOW / ПОТОК ДАННЫХ:
Router -> Service -> Repository -> Database
  DTO  ->  Entity ->    SQL     ->   Table
"""

from typing import Optional, Sequence
from fastapi import HTTPException, status

from domain.models import User
from domain.schemas import UserCreate, UserUpdate, UserInDB
from unit_of_work import UnitOfWork
from factories.user_factory import UserFactory


class UserService:
    """
    Service for User business logic / Сервис для бизнес-логики пользователей

    Orchestrates repositories and applies business rules.
    Оркеструет репозитории и применяет бизнес-правила.
    """

    async def create_user(self, user_data: UserCreate) -> UserInDB:
        """
        Create new user with business validation / Создать пользователя с бизнес-валидацией

        Business rules / Бизнес-правила:
        1. Username must be unique / Имя пользователя должно быть уникальным
        2. Email must be unique / Email должен быть уникальным
        3. Apply default values / Применить значения по умолчанию

        Args:
            user_data: Validated DTO from request / Валидированный DTO из запроса

        Returns:
            Created user DTO / Созданный DTO пользователя

        Raises:
            HTTPException: If username or email already exists / Если имя или email уже существуют
        """
        async with UnitOfWork() as uow:
            # Business validation: Check username uniqueness
            # Бизнес-валидация: Проверить уникальность имени
            if await uow.users.username_exists(user_data.username):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Username '{user_data.username}' already exists / Имя пользователя уже существует"
                )

            # Business validation: Check email uniqueness
            # Бизнес-валидация: Проверить уникальность email
            if await uow.users.email_exists(user_data.email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email '{user_data.email}' already exists / Email уже существует"
                )

            # Use factory to create entity / Использовать фабрику для создания сущности
            user = UserFactory.create_from_dto(user_data)

            # Persist through repository / Сохранить через репозиторий
            created_user = await uow.users.create(user)

            # Commit transaction / Закоммитить транзакцию
            await uow.commit()

            # Convert to DTO for response / Конвертировать в DTO для ответа
            return UserInDB.model_validate(created_user)

    async def get_user(self, user_id: int) -> UserInDB:
        """
        Get user by ID / Получить пользователя по ID

        Args:
            user_id: User ID / ID пользователя

        Returns:
            User DTO / DTO пользователя

        Raises:
            HTTPException: If user not found / Если пользователь не найден
        """
        async with UnitOfWork() as uow:
            user = await uow.users.get_by_id(user_id)

            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found / Пользователь с ID {user_id} не найден"
                )

            return UserInDB.model_validate(user)

    async def get_user_by_username(self, username: str) -> UserInDB:
        """
        Get user by username / Получить пользователя по имени

        Args:
            username: Username / Имя пользователя

        Returns:
            User DTO / DTO пользователя

        Raises:
            HTTPException: If user not found / Если пользователь не найден
        """
        async with UnitOfWork() as uow:
            user = await uow.users.get_by_username(username)

            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User '{username}' not found / Пользователь '{username}' не найден"
                )

            return UserInDB.model_validate(user)

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False
    ) -> tuple[Sequence[UserInDB], int]:
        """
        List users with pagination / Список пользователей с пагинацией

        Args:
            skip: Records to skip / Записей пропустить
            limit: Max records / Максимум записей
            active_only: Return only active users / Только активные пользователи

        Returns:
            Tuple of (users list, total count) / Кортеж (список пользователей, всего)
        """
        async with UnitOfWork() as uow:
            if active_only:
                users = await uow.users.get_active_users(skip, limit)
            else:
                users = await uow.users.get_all(skip, limit)

            total = await uow.users.count()

            # Convert to DTOs / Конвертировать в DTO
            user_dtos = [UserInDB.model_validate(user) for user in users]

            return user_dtos, total

    async def update_user(self, user_id: int, user_data: UserUpdate) -> UserInDB:
        """
        Update user with business validation / Обновить пользователя с бизнес-валидацией

        Business rules / Бизнес-правила:
        1. User must exist / Пользователь должен существовать
        2. If changing username, it must be unique / Если меняем имя, оно должно быть уникальным
        3. If changing email, it must be unique / Если меняем email, он должен быть уникальным

        Args:
            user_id: User ID / ID пользователя
            user_data: Fields to update / Поля для обновления

        Returns:
            Updated user DTO / Обновленный DTO пользователя

        Raises:
            HTTPException: If validation fails / Если валидация не прошла
        """
        async with UnitOfWork() as uow:
            # Check user exists / Проверить существование пользователя
            user = await uow.users.get_by_id(user_id)
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found / Пользователь с ID {user_id} не найден"
                )

            # Prepare update data / Подготовить данные для обновления
            update_data = user_data.model_dump(exclude_unset=True)

            # Business validation: Check username uniqueness if changing
            # Бизнес-валидация: Проверить уникальность имени при изменении
            if "username" in update_data:
                if await uow.users.username_exists(update_data["username"], exclude_id=user_id):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Username '{update_data['username']}' already exists / Имя уже существует"
                    )

            # Business validation: Check email uniqueness if changing
            # Бизнес-валидация: Проверить уникальность email при изменении
            if "email" in update_data:
                if await uow.users.email_exists(update_data["email"], exclude_id=user_id):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Email '{update_data['email']}' already exists / Email уже существует"
                    )

            # Update through repository / Обновить через репозиторий
            updated_user = await uow.users.update(user_id, **update_data)

            # Commit transaction / Закоммитить транзакцию
            await uow.commit()

            return UserInDB.model_validate(updated_user)

    async def delete_user(self, user_id: int) -> None:
        """
        Delete user / Удалить пользователя

        Args:
            user_id: User ID / ID пользователя

        Raises:
            HTTPException: If user not found / Если пользователь не найден
        """
        async with UnitOfWork() as uow:
            # Check user exists / Проверить существование
            if not await uow.users.exists(user_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found / Пользователь с ID {user_id} не найден"
                )

            # Delete through repository / Удалить через репозиторий
            await uow.users.delete(user_id)

            # Commit transaction / Закоммитить транзакцию
            await uow.commit()

    async def search_users(self, search_term: str, skip: int = 0, limit: int = 100) -> Sequence[UserInDB]:
        """
        Search users by term / Поиск пользователей по термину

        Args:
            search_term: Search term / Термин поиска
            skip: Records to skip / Записей пропустить
            limit: Max records / Максимум записей

        Returns:
            List of matching users / Список совпадающих пользователей
        """
        async with UnitOfWork() as uow:
            users = await uow.users.search_users(search_term, skip, limit)
            return [UserInDB.model_validate(user) for user in users]
