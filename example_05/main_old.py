"""
FastAPI Dependency Injection Example

This example demonstrates:
1. How FastAPI's Depends() mechanism works internally
2. Multi-level dependency chains
3. Service layer pattern with DI
4. Repository pattern with DI
5. Database session management via DI
6. Benefits for testing and maintainability

Key DI Concepts:
- Dependencies are functions/callables that FastAPI calls automatically
- Results are cached per request (same dependency called multiple times = same instance)
- Dependencies can depend on other dependencies (dependency chain)
- FastAPI handles cleanup (e.g., closing database sessions) automatically
"""

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, select
from typing import AsyncGenerator, Optional
from pydantic import BaseModel, ConfigDict
from contextlib import asynccontextmanager

# =============================================================================
# DATABASE SETUP
# =============================================================================

DATABASE_URL = "sqlite+aiosqlite:///./example_04.db"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    """User database model"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

app = FastAPI(title="Example 04: Dependency Injection")


# ============================================
# 1. ПРОСТЕЙШАЯ ЗАВИСИМОСТЬ - Функция
# ============================================

def get_db():
    """
    Базовая зависимость - создание и закрытие сессии БД

    Принцип работы:
    1. FastAPI вызывает функцию до выполнения роута
    2. yield передаёт значение в роут
    3. finally выполняется после роута (гарантированно)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/basic-di")
def basic_dependency_example(db: Session = Depends(get_db)):
    """
    Простейший пример DI
    FastAPI автоматически вызывает get_db() и передаёт результат
    """
    count = db.query(ProductModel).count()
    return {"message": "DI работает!", "products_count": count}


# ============================================
# 2. ЗАВИСИМОСТИ С ПАРАМЕТРАМИ
# ============================================

def get_current_user(
    token: str = Header(..., alias="X-Token"),
    db: Session = Depends(get_db)
):
    """
    Зависимость с параметрами

    Демонстрирует:
    - Получение заголовков через Header
    - Использование другой зависимости (get_db)
    - Валидация и авторизация
    """
    # В реальности тут проверка JWT токена
    if token != "secret-token":
        raise HTTPException(status_code=401, detail="Неверный токен")

    # Имитация поиска пользователя в БД
    user = {"user_id": 1, "username": "admin", "role": "admin"}
    return user


@app.get("/protected")
def protected_route(
    current_user: dict = Depends(get_current_user)
):
    """
    Защищённый роут - требует авторизации

    current_user автоматически заполняется результатом get_current_user()
    """
    return {
        "message": f"Привет, {current_user['username']}!",
        "user": current_user
    }


# ============================================
# 3. ВЛОЖЕННЫЕ ЗАВИСИМОСТИ (CHAIN)
# ============================================

def get_token(token: str = Header(..., alias="X-Token")):
    """Шаг 1: Получить токен из заголовка"""
    return token


def verify_token(token: str = Depends(get_token)):
    """
    Шаг 2: Проверить токен
    Использует зависимость get_token
    """
    if token != "secret-token":
        raise HTTPException(status_code=401, detail="Неверный токен")
    return token


def get_user_from_token(
    token: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Шаг 3: Получить пользователя по токену
    Использует зависимости verify_token и get_db

    Цепочка: get_token → verify_token → get_user_from_token
    """
    # В реальности: декодировать JWT и достать user_id
    user = {"user_id": 1, "username": "admin"}
    return user


@app.get("/nested-di")
def nested_dependency_example(
    user: dict = Depends(get_user_from_token)
):
    """
    Роут с цепочкой зависимостей

    FastAPI автоматически разрешает всю цепочку:
    get_token → verify_token → get_user_from_token → этот роут
    """
    return {"message": "Цепочка DI работает!", "user": user}


# ============================================
# 4. КЛАССЫ КАК ЗАВИСИМОСТИ
# ============================================

class Paginator:
    """
    Класс-зависимость для пагинации

    Преимущества:
    - Инкапсуляция логики
    - Переиспользование
    - Легко тестировать
    """

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Номер страницы"),
        page_size: int = Query(10, ge=1, le=100, description="Размер страницы")
    ):
        self.page = page
        self.page_size = page_size

    @property
    def skip(self) -> int:
        """Сколько записей пропустить"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Сколько записей взять"""
        return self.page_size


@app.get("/products")
def list_products(
    paginator: Paginator = Depends(),
    db: Session = Depends(get_db)
):
    """
    Использование класса как зависимости

    FastAPI создаёт экземпляр Paginator с параметрами из query
    """
    products = db.query(ProductModel)\
        .offset(paginator.skip)\
        .limit(paginator.limit)\
        .all()

    return {
        "page": paginator.page,
        "page_size": paginator.page_size,
        "products": [
            {"id": p.id, "name": p.name, "price": p.price}
            for p in products
        ]
    }


# ============================================
# 5. SERVICE LAYER С DEPENDENCY INJECTION
# ============================================

class ProductService:
    """
    Сервисный слой - бизнес-логика работы с товарами

    Принципы:
    - Отделение бизнес-логики от роутов
    - Инъекция зависимостей (БД сессия)
    - Переиспользование кода
    """

    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def get_product(self, product_id: int) -> ProductModel:
        """Получить товар по ID"""
        product = self.db.query(ProductModel)\
            .filter(ProductModel.id == product_id)\
            .first()

        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")

        return product

    def create_product(self, name: str, price: float, owner_id: int) -> ProductModel:
        """Создать товар с валидацией"""
        # Бизнес-правило: цена не может быть отрицательной
        if price < 0:
            raise HTTPException(status_code=400, detail="Цена не может быть отрицательной")

        product = ProductModel(name=name, price=price, owner_id=owner_id)
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)

        return product

    def update_price(self, product_id: int, new_price: float) -> ProductModel:
        """Обновить цену товара"""
        product = self.get_product(product_id)

        # Бизнес-правило: цена может изменяться не более чем на 50%
        price_change = abs(new_price - product.price) / product.price
        if price_change > 0.5:
            raise HTTPException(
                status_code=400,
                detail="Цена не может измениться более чем на 50%"
            )

        product.price = new_price
        self.db.commit()
        self.db.refresh(product)

        return product


@app.post("/products/service")
def create_product_with_service(
    name: str,
    price: float,
    user: dict = Depends(get_current_user),
    service: ProductService = Depends()
):
    """
    Создание товара через сервисный слой

    Преимущества:
    - Бизнес-логика в сервисе, не в роуте
    - Легко тестировать (мокаем сервис)
    - Переиспользование между роутами
    """
    product = service.create_product(
        name=name,
        price=price,
        owner_id=user["user_id"]
    )

    return {
        "message": "Товар создан через сервис",
        "product": {
            "id": product.id,
            "name": product.name,
            "price": product.price
        }
    }


@app.patch("/products/{product_id}/price")
def update_product_price(
    product_id: int,
    new_price: float,
    user: dict = Depends(get_current_user),
    service: ProductService = Depends()
):
    """Обновление цены через сервис с бизнес-правилами"""
    product = service.update_price(product_id, new_price)

    return {
        "message": "Цена обновлена",
        "product": {
            "id": product.id,
            "name": product.name,
            "old_price": product.price,
            "new_price": new_price
        }
    }


# ============================================
# 6. ЗАВИСИМОСТИ НА УРОВНЕ РОУТЕРА
# ============================================

def require_admin(user: dict = Depends(get_current_user)):
    """
    Проверка роли администратора

    Используется как зависимость роутера
    """
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Требуются права администратора")
    return user


from fastapi import APIRouter

admin_router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin)]  # Применяется ко всем роутам!
)


@admin_router.get("/stats")
def admin_stats(db: Session = Depends(get_db)):
    """
    Админский роут - require_admin применяется автоматически

    Не нужно указывать Depends(require_admin) в каждом роуте!
    """
    return {
        "total_products": db.query(ProductModel).count(),
        "message": "Доступно только админам"
    }


@admin_router.delete("/products/{product_id}")
def admin_delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Удаление товара (только админ)"""
    product = db.query(ProductModel)\
        .filter(ProductModel.id == product_id)\
        .first()

    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    db.delete(product)
    db.commit()

    return {"message": "Товар удалён", "product_id": product_id}


app.include_router(admin_router)


# ============================================
# 7. SUB-DEPENDENCIES (Подзависимости)
# ============================================

def get_query_params(
    search: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0)
):
    """Общие query параметры для фильтрации"""
    return {
        "search": search,
        "min_price": min_price,
        "max_price": max_price
    }


def build_product_filter(
    params: dict = Depends(get_query_params),
    db: Session = Depends(get_db)
):
    """
    Построение фильтра для товаров

    Использует подзависимость get_query_params
    """
    query = db.query(ProductModel)

    if params["search"]:
        query = query.filter(ProductModel.name.contains(params["search"]))

    if params["min_price"] is not None:
        query = query.filter(ProductModel.price >= params["min_price"])

    if params["max_price"] is not None:
        query = query.filter(ProductModel.price <= params["max_price"])

    return query


@app.get("/products/filtered")
def get_filtered_products(
    query = Depends(build_product_filter),
    paginator: Paginator = Depends()
):
    """
    Фильтрация с подзависимостями

    Цепочка:
    - get_query_params → build_product_filter
    - Paginator
    - Комбинация в роуте
    """
    products = query.offset(paginator.skip)\
        .limit(paginator.limit)\
        .all()

    return {
        "page": paginator.page,
        "products": [
            {"id": p.id, "name": p.name, "price": p.price}
            for p in products
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
