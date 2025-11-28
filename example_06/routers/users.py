"""
API Router for Users / API роутер для пользователей

This is the HTTP layer - handles requests and responses.
Это HTTP слой - обрабатывает запросы и ответы.

WHY THIN ROUTERS? / ЗАЧЕМ ТОНКИЕ РОУТЕРЫ?
1. Single Responsibility / Единственная ответственность
   - Router only handles HTTP concerns / Роутер только обрабатывает HTTP
   - Business logic in service layer / Бизнес-логика в слое сервисов

2. Testability / Тестируемость
   - Test business logic without HTTP / Тестировать логику без HTTP
   - Test HTTP layer separately / Тестировать HTTP слой отдельно

3. Reusability / Переиспользуемость
   - Same service can be used by CLI, background jobs, etc.
   - Тот же сервис можно использовать в CLI, фоновых задачах и т.д.

ROUTER RESPONSIBILITIES / ОТВЕТСТВЕННОСТЬ РОУТЕРА:
- Parse HTTP request / Разобрать HTTP запрос
- Validate request data (Pydantic does this) / Валидировать данные (Pydantic это делает)
- Call service layer / Вызвать слой сервисов
- Convert result to HTTP response / Конвертировать результат в HTTP ответ
- Handle HTTP status codes / Обработать HTTP статус коды
"""

from typing import Optional
from fastapi import APIRouter, status, Query

from domain.schemas import UserCreate, UserUpdate, UserResponse, UserList
from services.user_service import UserService

# Create router with prefix and tags / Создать роутер с префиксом и тегами
router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "User not found / Пользователь не найден"}}
)

# Create service instance / Создать экземпляр сервиса
# In production, use dependency injection / В продакшене использовать dependency injection
user_service = UserService()


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user / Создать пользователя",
    description="Create a new user with unique username and email / Создать пользователя с уникальным именем и email"
)
async def create_user(user_data: UserCreate) -> UserResponse:
    """
    Create new user / Создать нового пользователя

    Args:
        user_data: User creation data / Данные для создания пользователя

    Returns:
        Created user / Созданный пользователь

    Raises:
        400: Username or email already exists / Имя или email уже существуют
    """
    # Router is thin - just calls service / Роутер тонкий - просто вызывает сервис
    user = await user_service.create_user(user_data)
    return UserResponse.model_validate(user)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID / Получить пользователя по ID",
    description="Retrieve user information by ID / Получить информацию о пользователе по ID"
)
async def get_user(user_id: int) -> UserResponse:
    """
    Get user by ID / Получить пользователя по ID

    Args:
        user_id: User ID / ID пользователя

    Returns:
        User data / Данные пользователя

    Raises:
        404: User not found / Пользователь не найден
    """
    user = await user_service.get_user(user_id)
    return UserResponse.model_validate(user)


@router.get(
    "/username/{username}",
    response_model=UserResponse,
    summary="Get user by username / Получить пользователя по имени",
    description="Retrieve user information by username / Получить информацию по имени пользователя"
)
async def get_user_by_username(username: str) -> UserResponse:
    """
    Get user by username / Получить пользователя по имени

    Args:
        username: Username / Имя пользователя

    Returns:
        User data / Данные пользователя

    Raises:
        404: User not found / Пользователь не найден
    """
    user = await user_service.get_user_by_username(username)
    return UserResponse.model_validate(user)


@router.get(
    "/",
    response_model=UserList,
    summary="List users / Список пользователей",
    description="Get paginated list of users / Получить список пользователей с пагинацией"
)
async def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip / Количество записей пропустить"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return / Максимум записей вернуть"),
    active_only: bool = Query(False, description="Return only active users / Только активные пользователи")
) -> UserList:
    """
    List users with pagination / Список пользователей с пагинацией

    Args:
        skip: Records to skip / Записей пропустить
        limit: Max records (1-1000) / Максимум записей (1-1000)
        active_only: Filter active users / Фильтр активных пользователей

    Returns:
        Paginated user list / Список пользователей с пагинацией
    """
    users, total = await user_service.list_users(skip, limit, active_only)

    # Convert to response DTOs / Конвертировать в DTO ответов
    user_responses = [UserResponse.model_validate(user) for user in users]

    return UserList(total=total, users=user_responses)


@router.get(
    "/search/",
    response_model=list[UserResponse],
    summary="Search users / Поиск пользователей",
    description="Search users by username, email or full name / Поиск по имени, email или полному имени"
)
async def search_users(
    q: str = Query(..., min_length=1, description="Search query / Поисковый запрос"),
    skip: int = Query(0, ge=0, description="Number of records to skip / Количество записей пропустить"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return / Максимум записей вернуть")
) -> list[UserResponse]:
    """
    Search users / Поиск пользователей

    Args:
        q: Search query / Поисковый запрос
        skip: Records to skip / Записей пропустить
        limit: Max records / Максимум записей

    Returns:
        List of matching users / Список совпадающих пользователей
    """
    users = await user_service.search_users(q, skip, limit)
    return [UserResponse.model_validate(user) for user in users]


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user / Обновить пользователя",
    description="Update user information / Обновить информацию о пользователе"
)
async def update_user(user_id: int, user_data: UserUpdate) -> UserResponse:
    """
    Update user / Обновить пользователя

    Args:
        user_id: User ID / ID пользователя
        user_data: Fields to update / Поля для обновления

    Returns:
        Updated user / Обновленный пользователь

    Raises:
        404: User not found / Пользователь не найден
        400: Username or email already exists / Имя или email уже существуют
    """
    user = await user_service.update_user(user_id, user_data)
    return UserResponse.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user / Удалить пользователя",
    description="Delete user by ID / Удалить пользователя по ID"
)
async def delete_user(user_id: int) -> None:
    """
    Delete user / Удалить пользователя

    Args:
        user_id: User ID / ID пользователя

    Raises:
        404: User not found / Пользователь не найден
    """
    await user_service.delete_user(user_id)
    # Return 204 No Content / Вернуть 204 No Content
