"""
Factory Pattern for User Creation / Паттерн фабрики для создания пользователей

Encapsulates complex object creation logic.
Инкапсулирует сложную логику создания объектов.

WHY FACTORY? / ЗАЧЕМ ФАБРИКА?
1. Centralized Creation / Централизованное создание
   - Single place for object creation logic / Единое место для логики создания
   - Easy to modify creation process / Легко изменить процесс создания

2. Validation / Валидация
   - Business rules applied during creation / Бизнес-правила применяются при создании
   - Ensures valid objects / Гарантирует валидные объекты

3. Consistency / Согласованность
   - Objects created the same way / Объекты создаются одинаково
   - Default values handled properly / Значения по умолчанию обработаны правильно

4. Testing / Тестирование
   - Easy to create test objects / Легко создать тестовые объекты
   - Mock-friendly / Дружелюбно к mock-объектам
"""

from typing import Optional
from datetime import datetime

from domain.models import User
from domain.schemas import UserCreate


class UserFactory:
    """
    Factory for creating User entities / Фабрика для создания сущностей User

    Handles conversion from DTOs to domain models.
    Обрабатывает конвертацию из DTO в доменные модели.
    """

    @staticmethod
    def create_from_dto(dto: UserCreate) -> User:
        """
        Create User entity from DTO / Создать сущность User из DTO

        This method:
        1. Converts DTO to domain model / Конвертирует DTO в доменную модель
        2. Applies business rules / Применяет бизнес-правила
        3. Sets default values / Устанавливает значения по умолчанию

        Args:
            dto: UserCreate DTO with validated data / DTO UserCreate с валидными данными

        Returns:
            User entity ready for persistence / Сущность User готовая для сохранения
        """
        # Create User instance / Создать экземпляр User
        user = User(
            username=dto.username,
            email=dto.email,
            full_name=dto.full_name,
            is_active=dto.is_active
        )

        # Business rules can be applied here
        # Бизнес-правила могут быть применены здесь
        # For example: normalize email, validate username format, etc.
        # Например: нормализовать email, проверить формат username и т.д.

        return user

    @staticmethod
    def create_test_user(
        username: str = "testuser",
        email: str = "test@example.com",
        full_name: Optional[str] = "Test User",
        is_active: bool = True
    ) -> User:
        """
        Create test user with default values / Создать тестового пользователя со значениями по умолчанию

        Useful for testing and development.
        Полезно для тестирования и разработки.

        Args:
            username: Username / Имя пользователя
            email: Email address / Email адрес
            full_name: Full name / Полное имя
            is_active: Active status / Статус активности

        Returns:
            User entity with test data / Сущность User с тестовыми данными
        """
        return User(
            username=username,
            email=email,
            full_name=full_name,
            is_active=is_active
        )

    @staticmethod
    def create_admin_user(
        username: str,
        email: str,
        full_name: Optional[str] = None
    ) -> User:
        """
        Create admin user with specific defaults / Создать админа со специфичными значениями

        Example of specialized factory method.
        Пример специализированного фабричного метода.

        Args:
            username: Admin username / Имя пользователя админа
            email: Admin email / Email админа
            full_name: Admin full name / Полное имя админа

        Returns:
            User entity configured as admin / Сущность User настроенная как админ
        """
        user = User(
            username=username,
            email=email,
            full_name=full_name or f"Administrator {username}",
            is_active=True  # Admins always active / Админы всегда активны
        )

        # Additional admin-specific setup could go here
        # Дополнительная настройка админа может быть здесь

        return user


# Usage examples / Примеры использования:
"""
# In service layer / В слое сервисов:
from factories.user_factory import UserFactory

async def create_user(dto: UserCreate, uow: UnitOfWork):
    # Use factory to create entity / Используем фабрику для создания сущности
    user = UserFactory.create_from_dto(dto)

    # Persist through repository / Сохраняем через репозиторий
    created_user = await uow.users.create(user)
    await uow.commit()

    return created_user

# In tests / В тестах:
def test_user_creation():
    user = UserFactory.create_test_user(username="testuser")
    assert user.username == "testuser"
    assert user.is_active == True
"""
