"""
Example 01: Basic FastAPI Requests
===================================
Comprehensive tutorial covering fundamental FastAPI concepts:
- HTTP methods (GET, POST, PUT, DELETE)
- Path parameters and query parameters
- Request body handling
- Response models and status codes

Пример 01: Базовые запросы FastAPI
===================================
Полное руководство по основным концепциям FastAPI:
- HTTP методы (GET, POST, PUT, DELETE)
- Параметры пути и параметры запроса
- Обработка тела запроса
- Модели ответов и коды состояния
"""

from fastapi import FastAPI, HTTPException, Query, Path, status
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from enum import Enum

# Initialize FastAPI application
# Инициализация приложения FastAPI
app = FastAPI(
    title="FastAPI Basic Requests Tutorial",
    description="Comprehensive guide to basic FastAPI operations",
    version="1.0.0"
)


# ==============================================================================
# DATA MODELS (Pydantic Models)
# Модели данных (Pydantic модели)
# ==============================================================================

class ItemCategory(str, Enum):
    """
    Enum for item categories
    Перечисление категорий товаров
    """
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    FOOD = "food"
    BOOKS = "books"


class Item(BaseModel):
    """
    Item model for request/response
    Модель товара для запросов/ответов
    """
    name: str = Field(..., min_length=1, max_length=100, description="Item name")
    description: Optional[str] = Field(None, max_length=500, description="Item description")
    price: float = Field(..., gt=0, description="Item price (must be positive)")
    category: ItemCategory = Field(..., description="Item category")
    in_stock: bool = Field(default=True, description="Availability status")

    class Config:
        schema_extra = {
            "example": {
                "name": "Laptop",
                "description": "High-performance laptop",
                "price": 999.99,
                "category": "electronics",
                "in_stock": True
            }
        }


class ItemResponse(BaseModel):
    """
    Enhanced item model with ID for responses
    Расширенная модель товара с ID для ответов
    """
    id: int
    name: str
    description: Optional[str]
    price: float
    category: ItemCategory
    in_stock: bool


class User(BaseModel):
    """
    User model for registration/profile
    Модель пользователя для регистрации/профиля
    """
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    age: Optional[int] = Field(None, ge=18, le=120, description="Age must be 18 or above")

    class Config:
        schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "age": 25
            }
        }


class UserResponse(BaseModel):
    """
    User response model with ID
    Модель ответа пользователя с ID
    """
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str]
    age: Optional[int]


# ==============================================================================
# IN-MEMORY DATA STORAGE
# Хранилище данных в памяти
# ==============================================================================

# Simulated database for items
# Имитация базы данных для товаров
items_db: dict[int, dict] = {
    1: {
        "id": 1,
        "name": "Laptop",
        "description": "High-performance laptop",
        "price": 999.99,
        "category": "electronics",
        "in_stock": True
    },
    2: {
        "id": 2,
        "name": "T-Shirt",
        "description": "Cotton t-shirt",
        "price": 19.99,
        "category": "clothing",
        "in_stock": True
    },
    3: {
        "id": 3,
        "name": "Python Book",
        "description": "Learn Python in 30 days",
        "price": 29.99,
        "category": "books",
        "in_stock": False
    }
}

# Simulated database for users
# Имитация базы данных для пользователей
users_db: dict[int, dict] = {
    1: {
        "id": 1,
        "username": "alice",
        "email": "alice@example.com",
        "full_name": "Alice Smith",
        "age": 28
    }
}

# Counters for auto-incrementing IDs
# Счетчики для автоинкрементных ID
next_item_id = 4
next_user_id = 2


# ==============================================================================
# BASIC GET REQUESTS
# Базовые GET запросы
# ==============================================================================

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - basic GET request
    Корневой эндпоинт - базовый GET запрос

    Returns a welcome message
    Возвращает приветственное сообщение
    """
    return {
        "message": "Welcome to FastAPI Basic Requests Tutorial",
        "documentation": "/docs",
        "version": "1.0.0"
    }


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    """
    Health check endpoint
    Эндпоинт проверки здоровья приложения

    Used to verify that the API is running
    Используется для проверки работоспособности API
    """
    return {
        "status": "healthy",
        "service": "FastAPI Tutorial"
    }


# ==============================================================================
# GET REQUESTS WITH PATH PARAMETERS
# GET запросы с параметрами пути
# ==============================================================================

@app.get("/items/{item_id}", response_model=ItemResponse, tags=["Items"])
async def get_item(
    item_id: int = Path(..., gt=0, description="The ID of the item to retrieve")
):
    """
    Get a specific item by ID (Path Parameter)
    Получить конкретный товар по ID (параметр пути)

    Path parameters are part of the URL path
    Параметры пути являются частью URL-адреса

    Example: /items/1
    """
    if item_id not in items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found"
        )

    return items_db[item_id]


@app.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def get_user(
    user_id: int = Path(..., gt=0, description="The ID of the user to retrieve")
):
    """
    Get a specific user by ID
    Получить конкретного пользователя по ID

    Example: /users/1
    """
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )

    return users_db[user_id]


# ==============================================================================
# GET REQUESTS WITH QUERY PARAMETERS
# GET запросы с параметрами запроса
# ==============================================================================

@app.get("/items", response_model=List[ItemResponse], tags=["Items"])
async def list_items(
    category: Optional[ItemCategory] = Query(None, description="Filter by category"),
    in_stock: Optional[bool] = Query(None, description="Filter by availability"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip")
):
    """
    List items with optional filtering (Query Parameters)
    Список товаров с опциональной фильтрацией (параметры запроса)

    Query parameters are added after ? in the URL
    Параметры запроса добавляются после ? в URL

    Examples:
    - /items?category=electronics
    - /items?in_stock=true&min_price=10&max_price=100
    - /items?limit=5&offset=10
    """
    # Start with all items
    # Начинаем со всех товаров
    filtered_items = list(items_db.values())

    # Apply category filter
    # Применяем фильтр по категории
    if category:
        filtered_items = [
            item for item in filtered_items
            if item["category"] == category.value
        ]

    # Apply stock filter
    # Применяем фильтр по наличию
    if in_stock is not None:
        filtered_items = [
            item for item in filtered_items
            if item["in_stock"] == in_stock
        ]

    # Apply price filters
    # Применяем фильтры по цене
    if min_price is not None:
        filtered_items = [
            item for item in filtered_items
            if item["price"] >= min_price
        ]

    if max_price is not None:
        filtered_items = [
            item for item in filtered_items
            if item["price"] <= max_price
        ]

    # Apply pagination
    # Применяем пагинацию
    paginated_items = filtered_items[offset:offset + limit]

    return paginated_items


@app.get("/search", tags=["Search"])
async def search_items(
    query: str = Query(..., min_length=1, max_length=100, description="Search query"),
    search_in: List[str] = Query(["name", "description"], description="Fields to search in")
):
    """
    Search items by keyword
    Поиск товаров по ключевому слову

    Demonstrates multiple query parameters including list parameters
    Демонстрирует множественные параметры запроса, включая списочные параметры

    Example: /search?query=laptop&search_in=name&search_in=description
    """
    results = []
    query_lower = query.lower()

    for item in items_db.values():
        # Check if query matches any of the specified fields
        # Проверяем, соответствует ли запрос каким-либо указанным полям
        if "name" in search_in and query_lower in item["name"].lower():
            results.append(item)
        elif "description" in search_in and item["description"] and query_lower in item["description"].lower():
            results.append(item)

    return {
        "query": query,
        "searched_fields": search_in,
        "results_count": len(results),
        "results": results
    }


# ==============================================================================
# POST REQUESTS - Creating Resources
# POST запросы - создание ресурсов
# ==============================================================================

@app.post("/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED, tags=["Items"])
async def create_item(item: Item):
    """
    Create a new item (POST with Request Body)
    Создать новый товар (POST с телом запроса)

    Request body is automatically validated using Pydantic model
    Тело запроса автоматически валидируется с использованием модели Pydantic

    Returns 201 Created status code
    Возвращает код состояния 201 Created
    """
    global next_item_id

    # Create new item with auto-incremented ID
    # Создаем новый товар с автоинкрементным ID
    new_item = {
        "id": next_item_id,
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "category": item.category.value,
        "in_stock": item.in_stock
    }

    items_db[next_item_id] = new_item
    next_item_id += 1

    return new_item


@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Users"])
async def create_user(user: User):
    """
    Create a new user
    Создать нового пользователя

    Validates email format and other constraints automatically
    Автоматически валидирует формат email и другие ограничения
    """
    global next_user_id

    # Check if username already exists
    # Проверяем, существует ли уже такое имя пользователя
    for existing_user in users_db.values():
        if existing_user["username"] == user.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username '{user.username}' already exists"
            )
        if existing_user["email"] == user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{user.email}' already registered"
            )

    # Create new user
    # Создаем нового пользователя
    new_user = {
        "id": next_user_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "age": user.age
    }

    users_db[next_user_id] = new_user
    next_user_id += 1

    return new_user


# ==============================================================================
# PUT REQUESTS - Full Updates
# PUT запросы - полное обновление
# ==============================================================================

@app.put("/items/{item_id}", response_model=ItemResponse, tags=["Items"])
async def update_item(
    item_id: int = Path(..., gt=0, description="ID of item to update"),
    item: Item = ...
):
    """
    Update an existing item completely (PUT Request)
    Полностью обновить существующий товар (PUT запрос)

    PUT replaces the entire resource
    PUT заменяет весь ресурс целиком

    Combines path parameter (item_id) with request body (item)
    Комбинирует параметр пути (item_id) с телом запроса (item)
    """
    if item_id not in items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found"
        )

    # Update the item completely
    # Полностью обновляем товар
    updated_item = {
        "id": item_id,
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "category": item.category.value,
        "in_stock": item.in_stock
    }

    items_db[item_id] = updated_item

    return updated_item


@app.put("/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def update_user(
    user_id: int = Path(..., gt=0, description="ID of user to update"),
    user: User = ...
):
    """
    Update an existing user completely
    Полностью обновить существующего пользователя
    """
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )

    # Check for duplicate username/email (excluding current user)
    # Проверяем дубликаты username/email (исключая текущего пользователя)
    for uid, existing_user in users_db.items():
        if uid != user_id:
            if existing_user["username"] == user.username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Username '{user.username}' already exists"
                )
            if existing_user["email"] == user.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email '{user.email}' already registered"
                )

    # Update user
    # Обновляем пользователя
    updated_user = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "age": user.age
    }

    users_db[user_id] = updated_user

    return updated_user


# ==============================================================================
# DELETE REQUESTS - Removing Resources
# DELETE запросы - удаление ресурсов
# ==============================================================================

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Items"])
async def delete_item(
    item_id: int = Path(..., gt=0, description="ID of item to delete")
):
    """
    Delete an item (DELETE Request)
    Удалить товар (DELETE запрос)

    Returns 204 No Content on successful deletion
    Возвращает 204 No Content при успешном удалении
    """
    if item_id not in items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found"
        )

    # Delete the item
    # Удаляем товар
    del items_db[item_id]

    # 204 No Content - no response body needed
    # 204 No Content - тело ответа не требуется
    return None


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Users"])
async def delete_user(
    user_id: int = Path(..., gt=0, description="ID of user to delete")
):
    """
    Delete a user
    Удалить пользователя
    """
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )

    # Delete the user
    # Удаляем пользователя
    del users_db[user_id]

    return None


# ==============================================================================
# ADDITIONAL EXAMPLES - Advanced Patterns
# Дополнительные примеры - продвинутые паттерны
# ==============================================================================

@app.get("/stats", tags=["Statistics"])
async def get_statistics():
    """
    Get database statistics
    Получить статистику базы данных

    Demonstrates aggregation and data processing
    Демонстрирует агрегацию и обработку данных
    """
    total_items = len(items_db)
    in_stock_items = sum(1 for item in items_db.values() if item["in_stock"])

    # Category statistics
    # Статистика по категориям
    category_counts = {}
    total_value = 0.0

    for item in items_db.values():
        category = item["category"]
        category_counts[category] = category_counts.get(category, 0) + 1
        total_value += item["price"]

    return {
        "total_items": total_items,
        "in_stock": in_stock_items,
        "out_of_stock": total_items - in_stock_items,
        "total_users": len(users_db),
        "category_distribution": category_counts,
        "total_inventory_value": round(total_value, 2),
        "average_price": round(total_value / total_items, 2) if total_items > 0 else 0
    }


@app.post("/items/{item_id}/toggle-stock", response_model=ItemResponse, tags=["Items"])
async def toggle_item_stock(
    item_id: int = Path(..., gt=0, description="ID of item to toggle stock status")
):
    """
    Toggle item stock status
    Переключить статус наличия товара

    Demonstrates POST for actions (not just resource creation)
    Демонстрирует POST для действий (не только создания ресурсов)
    """
    if item_id not in items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found"
        )

    # Toggle the in_stock status
    # Переключаем статус наличия
    items_db[item_id]["in_stock"] = not items_db[item_id]["in_stock"]

    return items_db[item_id]


# ==============================================================================
# RUNNING THE APPLICATION
# Запуск приложения
# ==============================================================================

if __name__ == "__main__":
    import uvicorn

    """
    To run this application:
    Для запуска этого приложения:

    1. Install dependencies:
       pip install fastapi uvicorn pydantic[email]

    2. Run with uvicorn:
       uvicorn main:app --reload

    3. Open interactive documentation:
       http://127.0.0.1:8000/docs (Swagger UI)
       http://127.0.0.1:8000/redoc (ReDoc)

    4. Test endpoints using curl or the interactive docs:

       GET all items:
       curl http://127.0.0.1:8000/items

       GET specific item:
       curl http://127.0.0.1:8000/items/1

       POST create item:
       curl -X POST http://127.0.0.1:8000/items \
            -H "Content-Type: application/json" \
            -d '{"name":"Phone","price":599.99,"category":"electronics"}'

       PUT update item:
       curl -X PUT http://127.0.0.1:8000/items/1 \
            -H "Content-Type: application/json" \
            -d '{"name":"Gaming Laptop","price":1299.99,"category":"electronics"}'

       DELETE item:
       curl -X DELETE http://127.0.0.1:8000/items/1
    """

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
