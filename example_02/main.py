"""
Example 02: Pydantic BaseModel и валидация данных
Example 02: Pydantic BaseModel and Data Validation

Этот пример демонстрирует:
This example demonstrates:
1. Базовое использование BaseModel / Basic BaseModel usage
2. Валидацию полей (Field, field_validator) / Field validation
3. Вложенные модели / Nested models
4. Опциональные поля и значения по умолчанию / Optional fields and default values
5. Конфигурация моделей (ConfigDict) / Model configuration
6. Примеры валидации данных / Data validation examples
7. Обработка ошибок валидации / Validation error handling
"""

from datetime import datetime
from typing import Optional, List, Literal
from enum import Enum

from fastapi import FastAPI, HTTPException, status, Path
from pydantic import (
    BaseModel,
    Field,
    EmailStr,
    HttpUrl,
    field_validator,
    model_validator,
    ConfigDict,
)

app = FastAPI(
    title="Pydantic BaseModel Example",
    description="Comprehensive example of Pydantic models with validation",
    version="2.0.0",
)


# =============================================================================
# 1. БАЗОВАЯ МОДЕЛЬ / BASIC MODEL
# =============================================================================

class SimpleUser(BaseModel):
    """
    Простая модель пользователя с базовыми полями
    Simple user model with basic fields
    """
    id: int
    name: str
    email: EmailStr  # Автоматическая валидация email / Automatic email validation
    is_active: bool = True  # Значение по умолчанию / Default value


# =============================================================================
# 2. ПРОДВИНУТАЯ ВАЛИДАЦИЯ ПОЛЕЙ / ADVANCED FIELD VALIDATION
# =============================================================================

class UserRole(str, Enum):
    """
    Перечисление ролей пользователя
    User role enumeration
    """
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class AdvancedUser(BaseModel):
    """
    Продвинутая модель с валидацией полей через Field и валидаторы
    Advanced model with Field validation and validators
    """
    # ConfigDict заменяет вложенный класс Config в Pydantic v2
    # ConfigDict replaces nested Config class in Pydantic v2
    model_config = ConfigDict(
        str_strip_whitespace=True,  # Убирать пробелы / Strip whitespace
        validate_assignment=True,  # Валидировать при присваивании / Validate on assignment
        str_min_length=1,  # Минимальная длина строк / Minimum string length
    )

    # Использование Field для дополнительных ограничений
    # Using Field for additional constraints
    id: int = Field(..., gt=0, description="User ID must be positive")
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Username: 3-50 chars, alphanumeric, _, -"
    )
    email: EmailStr = Field(..., description="Valid email address")
    age: Optional[int] = Field(
        None,
        ge=0,
        le=120,
        description="Age between 0 and 120"
    )
    role: UserRole = Field(default=UserRole.USER, description="User role")
    website: Optional[HttpUrl] = Field(None, description="User website URL")
    tags: List[str] = Field(default_factory=list, max_length=10)

    # Field validator для пользовательской валидации (Pydantic v2)
    # Field validator for custom validation (Pydantic v2)
    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        """
        Проверка, что username содержит только допустимые символы
        Check that username contains only allowed characters
        """
        if not v:
            raise ValueError('Username cannot be empty')
        if v.lower() in ['admin', 'root', 'system']:
            raise ValueError('Reserved username')
        return v

    @field_validator('age')
    @classmethod
    def check_age_realistic(cls, v: Optional[int]) -> Optional[int]:
        """
        Дополнительная проверка возраста
        Additional age validation
        """
        if v is not None and v > 120:
            raise ValueError('Age seems unrealistic')
        return v

    # Model validator для валидации на уровне всей модели
    # Model validator for model-level validation
    @model_validator(mode='after')
    def check_admin_has_email(self) -> 'AdvancedUser':
        """
        Проверка, что у администратора есть email
        Check that admin has email
        """
        if self.role == UserRole.ADMIN and not self.email:
            raise ValueError('Admin must have email')
        return self


# =============================================================================
# 3. ВЛОЖЕННЫЕ МОДЕЛИ / NESTED MODELS
# =============================================================================

class Address(BaseModel):
    """
    Модель адреса
    Address model
    """
    street: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1)
    country: str = Field(..., min_length=2, max_length=2, description="ISO country code")
    zip_code: Optional[str] = Field(None, pattern=r"^\d{5,10}$")

    @field_validator('country')
    @classmethod
    def country_uppercase(cls, v: str) -> str:
        """Привести код страны к верхнему регистру / Convert country code to uppercase"""
        return v.upper()


class ContactInfo(BaseModel):
    """
    Контактная информация
    Contact information
    """
    phone: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{1,14}$")
    email: EmailStr
    telegram: Optional[str] = Field(None, pattern=r"^@[a-zA-Z0-9_]{5,32}$")


class UserProfile(BaseModel):
    """
    Профиль пользователя с вложенными моделями
    User profile with nested models
    """
    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=False,
    )

    user: AdvancedUser  # Вложенная модель / Nested model
    address: Optional[Address] = None  # Опциональная вложенная модель / Optional nested model
    contacts: ContactInfo  # Обязательная вложенная модель / Required nested model
    created_at: datetime = Field(default_factory=datetime.now)
    bio: Optional[str] = Field(None, max_length=500)

    @model_validator(mode='after')
    def validate_profile_completeness(self) -> 'UserProfile':
        """
        Проверка полноты профиля для администраторов
        Check profile completeness for admins
        """
        if self.user.role == UserRole.ADMIN:
            if not self.address:
                raise ValueError('Admin must have address')
            if not self.bio:
                raise ValueError('Admin must have bio')
        return self


# =============================================================================
# 4. МОДЕЛИ ДЛЯ ЗАПРОСОВ И ОТВЕТОВ / REQUEST AND RESPONSE MODELS
# =============================================================================

class UserCreateRequest(BaseModel):
    """
    Модель для создания пользователя
    Model for user creation
    """
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=120)
    role: UserRole = UserRole.USER

    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        """
        Проверка сложности пароля
        Password strength validation
        """
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v


class UserUpdateRequest(BaseModel):
    """
    Модель для обновления пользователя (все поля опциональные)
    Model for user update (all fields optional)
    """
    model_config = ConfigDict(
        extra='forbid',  # Запретить дополнительные поля / Forbid extra fields
    )

    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    age: Optional[int] = Field(None, ge=0, le=120)
    role: Optional[UserRole] = None
    website: Optional[HttpUrl] = None


class UserResponse(BaseModel):
    """
    Модель ответа с данными пользователя (без пароля)
    Response model with user data (without password)
    """
    id: int
    username: str
    email: EmailStr
    age: Optional[int]
    role: UserRole
    website: Optional[HttpUrl]
    created_at: datetime
    is_active: bool


class ErrorResponse(BaseModel):
    """
    Стандартная модель ошибки
    Standard error model
    """
    error: str
    detail: Optional[str] = None
    field: Optional[str] = None


# =============================================================================
# 5. ХРАНИЛИЩЕ ДАННЫХ (В ПАМЯТИ) / DATA STORAGE (IN-MEMORY)
# =============================================================================

# Простое хранилище пользователей в памяти
# Simple in-memory user storage
users_db: dict[int, UserResponse] = {}
user_id_counter = 1


# =============================================================================
# 6. API ENDPOINTS
# =============================================================================

@app.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user",
    description="Create a new user with validation"
)
async def create_user(user_data: UserCreateRequest) -> UserResponse:
    """
    Создание нового пользователя
    Create new user

    Pydantic автоматически валидирует входные данные
    Pydantic automatically validates input data
    """
    global user_id_counter

    # Проверка уникальности email
    # Check email uniqueness
    for user in users_db.values():
        if user.email == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email {user_data.email} already exists"
            )

    # Создание пользователя
    # Create user
    new_user = UserResponse(
        id=user_id_counter,
        username=user_data.username,
        email=user_data.email,
        age=user_data.age,
        role=user_data.role,
        website=None,
        created_at=datetime.now(),
        is_active=True
    )

    users_db[user_id_counter] = new_user
    user_id_counter += 1

    return new_user


@app.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Retrieve user information by ID"
)
async def get_user(user_id: int = Path(..., gt=0)) -> UserResponse:
    """
    Получение пользователя по ID
    Get user by ID
    """
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )

    return users_db[user_id]


@app.get(
    "/users",
    response_model=List[UserResponse],
    summary="List all users",
    description="Retrieve all users with optional role filtering"
)
async def list_users(
    role: Optional[UserRole] = None,
    is_active: bool = True
) -> List[UserResponse]:
    """
    Получение списка пользователей с фильтрацией
    Get list of users with filtering
    """
    users = list(users_db.values())

    if role:
        users = [u for u in users if u.role == role]

    users = [u for u in users if u.is_active == is_active]

    return users


@app.patch(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    description="Partially update user information"
)
async def update_user(
    user_id: int = Path(..., gt=0),
    update_data: UserUpdateRequest = None
) -> UserResponse:
    """
    Частичное обновление пользователя
    Partial user update

    Pydantic автоматически валидирует только предоставленные поля
    Pydantic automatically validates only provided fields
    """
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )

    user = users_db[user_id]

    # Обновляем только предоставленные поля (exclude_unset=True)
    # Update only provided fields (exclude_unset=True)
    update_dict = update_data.model_dump(exclude_unset=True)

    for field, value in update_dict.items():
        setattr(user, field, value)

    return user


@app.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description="Delete user by ID"
)
async def delete_user(user_id: int = Path(..., gt=0)) -> None:
    """
    Удаление пользователя
    Delete user
    """
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )

    del users_db[user_id]


@app.post(
    "/users/{user_id}/profile",
    response_model=UserProfile,
    status_code=status.HTTP_201_CREATED,
    summary="Create user profile",
    description="Create a complete user profile with nested models"
)
async def create_profile(
    user_id: int,
    address: Optional[Address] = None,
    contacts: ContactInfo = None,
    bio: Optional[str] = None
) -> UserProfile:
    """
    Создание профиля пользователя с вложенными моделями
    Create user profile with nested models

    Демонстрирует валидацию вложенных моделей
    Demonstrates nested model validation
    """
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )

    user_response = users_db[user_id]

    # Преобразуем UserResponse в AdvancedUser для профиля
    # Convert UserResponse to AdvancedUser for profile
    advanced_user = AdvancedUser(
        id=user_response.id,
        username=user_response.username,
        email=user_response.email,
        age=user_response.age,
        role=user_response.role,
        website=user_response.website,
        tags=[]
    )

    # Создаем профиль с валидацией вложенных моделей
    # Create profile with nested model validation
    profile = UserProfile(
        user=advanced_user,
        address=address,
        contacts=contacts,
        bio=bio
    )

    return profile


@app.get(
    "/validation/demo",
    summary="Validation examples",
    description="Demonstrates various validation scenarios"
)
async def validation_demo():
    """
    Демонстрация примеров валидации
    Validation examples demonstration
    """
    examples = {
        "valid_email": {
            "input": "user@example.com",
            "valid": True
        },
        "invalid_email": {
            "input": "not-an-email",
            "valid": False,
            "error": "Invalid email format"
        },
        "valid_age": {
            "input": 25,
            "valid": True,
            "constraints": "0 <= age <= 120"
        },
        "invalid_age": {
            "input": 200,
            "valid": False,
            "error": "Age must be <= 120"
        },
        "valid_username": {
            "input": "john_doe",
            "valid": True,
            "constraints": "3-50 chars, alphanumeric + _ -"
        },
        "invalid_username": {
            "input": "ab",
            "valid": False,
            "error": "Username too short (min 3 chars)"
        },
        "reserved_username": {
            "input": "admin",
            "valid": False,
            "error": "Reserved username"
        },
        "password_validation": {
            "valid_password": "MyPass123",
            "requirements": [
                "min 8 characters",
                "at least 1 uppercase",
                "at least 1 lowercase",
                "at least 1 digit"
            ]
        }
    }

    return {
        "message": "Validation examples",
        "pydantic_version": "2.x",
        "examples": examples,
        "documentation": "See model definitions for validation rules"
    }


# =============================================================================
# 7. ОБРАБОТКА ОШИБОК ВАЛИДАЦИИ / VALIDATION ERROR HANDLING
# =============================================================================

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """
    Пользовательская обработка ошибок валидации
    Custom validation error handling

    Преобразует ошибки Pydantic в понятный формат
    Converts Pydantic errors to readable format
    """
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": "Input data validation failed",
            "errors": errors
        }
    )


# =============================================================================
# 8. ИНФОРМАЦИОННЫЕ ENDPOINTS / INFORMATION ENDPOINTS
# =============================================================================

@app.get("/", summary="Root endpoint")
async def root():
    """
    Корневой endpoint с информацией о примере
    Root endpoint with example information
    """
    return {
        "example": "02 - Pydantic BaseModel и валидация",
        "description": "Comprehensive Pydantic validation examples",
        "features": [
            "Basic BaseModel usage",
            "Field validation with Field()",
            "Custom validators (@field_validator)",
            "Model validators (@model_validator)",
            "Nested models",
            "Optional fields and defaults",
            "Model configuration (ConfigDict)",
            "Request/Response models",
            "Custom error handling"
        ],
        "pydantic_version": "2.x",
        "endpoints": {
            "POST /users": "Create user with validation",
            "GET /users/{id}": "Get user by ID",
            "GET /users": "List users with filtering",
            "PATCH /users/{id}": "Update user",
            "DELETE /users/{id}": "Delete user",
            "POST /users/{id}/profile": "Create profile with nested models",
            "GET /validation/demo": "Validation examples"
        },
        "docs": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }


# =============================================================================
# ЗАПУСК ПРИЛОЖЕНИЯ / RUN APPLICATION
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║  Example 02: Pydantic BaseModel and Validation                ║
    ║  Пример 02: Pydantic BaseModel и валидация данных             ║
    ╠════════════════════════════════════════════════════════════════╣
    ║  Features / Возможности:                                       ║
    ║  ✓ BaseModel usage                                            ║
    ║  ✓ Field validation with Field()                              ║
    ║  ✓ Custom validators                                          ║
    ║  ✓ Nested models                                              ║
    ║  ✓ Model configuration                                        ║
    ║  ✓ Request/Response models                                    ║
    ║  ✓ Error handling                                             ║
    ╠════════════════════════════════════════════════════════════════╣
    ║  API Documentation:                                            ║
    ║  • Swagger UI: http://localhost:8000/docs                     ║
    ║  • ReDoc:      http://localhost:8000/redoc                    ║
    ╚════════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
