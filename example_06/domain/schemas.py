"""
DTOs (Data Transfer Objects) / Объекты передачи данных

This layer defines how data is transferred between layers and to/from API.
Этот слой определяет, как данные передаются между слоями и в/из API.

WHY DTOs? / ЗАЧЕМ DTO?
1. Validation / Валидация - Pydantic validates input automatically
2. Serialization / Сериализация - Convert Python objects to JSON
3. Decoupling / Разделение - API schema != Database schema
4. Documentation / Документация - Auto-generate OpenAPI docs
5. Security / Безопасность - Control what data is exposed

PATTERN / ПАТТЕРН:
- Create = Data needed to create entity / Данные для создания сущности
- Update = Data that can be updated / Данные для обновления
- InDB = Complete database record / Полная запись из БД
- Response = Data returned to client / Данные, возвращаемые клиенту
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserCreate(BaseModel):
    """
    DTO for creating a new user / DTO для создания нового пользователя

    Contains only fields needed for user creation.
    Содержит только поля, необходимые для создания пользователя.

    Used in: POST /users
    Используется в: POST /users
    """
    username: str = Field(
        ...,  # Required field / Обязательное поле
        min_length=3,
        max_length=100,
        description="Unique username / Уникальное имя пользователя"
    )
    email: EmailStr = Field(
        ...,
        description="User email address / Email адрес пользователя"
    )
    full_name: Optional[str] = Field(
        None,
        max_length=255,
        description="User's full name / Полное имя пользователя"
    )
    is_active: bool = Field(
        default=True,
        description="Whether user is active / Активен ли пользователь"
    )


class UserUpdate(BaseModel):
    """
    DTO for updating user / DTO для обновления пользователя

    All fields are optional - update only what's provided.
    Все поля опциональны - обновляем только то, что передано.

    Used in: PATCH /users/{id}
    Используется в: PATCH /users/{id}
    """
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class UserInDB(BaseModel):
    """
    DTO representing database record / DTO представляющий запись из БД

    Contains all fields from database including system fields.
    Содержит все поля из БД, включая системные поля.

    Used internally between repository and service layers.
    Используется внутри между слоями repository и service.
    """
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Pydantic v2 configuration / Конфигурация Pydantic v2
    model_config = ConfigDict(
        from_attributes=True,  # Allow creation from ORM objects / Разрешить создание из ORM объектов
        json_schema_extra={
            "example": {
                "id": 1,
                "username": "johndoe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "is_active": True,
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T12:00:00"
            }
        }
    )


class UserResponse(BaseModel):
    """
    DTO for API responses / DTO для ответов API

    Contains only data that should be exposed to clients.
    Содержит только данные, которые должны быть доступны клиентам.

    Note: We exclude sensitive fields and can add computed fields.
    Примечание: Исключаем чувствительные поля и можем добавить вычисляемые поля.

    Used in: All GET endpoints
    Используется в: Все GET эндпоинты
    """
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "username": "johndoe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "is_active": True,
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T12:00:00"
            }
        }
    )


class UserList(BaseModel):
    """
    DTO for paginated list of users / DTO для списка пользователей с пагинацией

    Wraps list of users with metadata.
    Оборачивает список пользователей с метаданными.
    """
    total: int = Field(description="Total number of users / Общее количество пользователей")
    users: list[UserResponse] = Field(description="List of users / Список пользователей")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 2,
                "users": [
                    {
                        "id": 1,
                        "username": "johndoe",
                        "email": "john@example.com",
                        "full_name": "John Doe",
                        "is_active": True,
                        "created_at": "2024-01-01T12:00:00",
                        "updated_at": "2024-01-01T12:00:00"
                    }
                ]
            }
        }
    )
