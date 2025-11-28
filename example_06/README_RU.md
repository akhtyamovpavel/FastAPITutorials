# Пример 06: Полная DDD архитектура с Async SQLAlchemy 2.0

**[🇬🇧 English version](README.md)**

## 📚 Что изучаем

Полная production-ready архитектура:
- ✅ **100% Async code** (все операции асинхронные!)
- ✅ **SQLAlchemy 2.0** с `db.execute()` и `mapped_column`
- ✅ **DAO** (Data Access Objects) - SQLAlchemy модели
- ✅ **DTO** (Data Transfer Objects) - Pydantic схемы
- ✅ **Repositories** - абстракция доступа к данным
- ✅ **Services** - бизнес-логика
- ✅ **Factories** - создание объектов
- ✅ **UnitOfWork** - управление транзакциями
- ✅ **Routers** - тонкий HTTP слой
- ✅ **Clean Architecture** principles

## 🏗️ Архитектура слоёв

```
┌─────────────────────────────────────────┐
│    Presentation Layer (HTTP)            │
│    routers/users.py                     │  FastAPI routes
├─────────────────────────────────────────┤
│    Application Layer (Orchestration)    │
│    services/user_service.py             │  Business logic
├─────────────────────────────────────────┤
│    Unit of Work (Transactions)          │
│    unit_of_work.py                      │  Transaction management
├─────────────────────────────────────────┤
│    Repository Layer (Data Access)       │
│    repositories/user_repository.py      │  Database queries
├─────────────────────────────────────────┤
│    Domain Layer (Core Business)         │
│    domain/models.py (DAO)               │  SQLAlchemy models
│    domain/schemas.py (DTO)              │  Pydantic schemas
├─────────────────────────────────────────┤
│    Factory Pattern (Object Creation)    │
│    factories/user_factory.py            │  Entity creation
├─────────────────────────────────────────┤
│    Infrastructure (Database)            │
│    database.py                          │  Async SQLAlchemy setup
└─────────────────────────────────────────┘
```

---

## 🎯 КРИТИЧЕСКИ ВАЖНО: Все операции Async!

### ✅ Этот пример использует ТОЛЬКО async:

```python
# ✅ Async database setup
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine("sqlite+aiosqlite:///./example_06.db")

# ✅ Async repository methods
class UserRepository:
    async def get(self, user_id: int) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

# ✅ Async service methods
class UserService:
    async def create_user(self, data: UserCreate) -> User:
        return await self.repository.add(user)

# ✅ Async routes
@router.post("/users")
async def create(user: UserCreate, service: UserService = Depends()):
    return await service.create_user(user)
```

### ❌ НЕ используется синхронный код:

```python
# ❌ НЕПРАВИЛЬНО - НЕ используется в этом примере!
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

engine = create_engine("sqlite:///./db.db")  # Sync!
db = Session(engine)  # Sync!
user = db.query(User).first()  # Sync!
```

---

## ⚡ SQLAlchemy 2.0 - Современный API

### ✅ Используется ТОЛЬКО новый синтаксис:

```python
# ✅ Modern ORM models
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    username: Mapped[str] = mapped_column(String)

# ✅ Modern query API
result = await db.execute(
    select(User).where(User.email == email)
)
user = result.scalar_one_or_none()

# ✅ For multiple results
result = await db.execute(
    select(User).offset(skip).limit(limit)
)
users = result.scalars().all()
```

### ❌ НЕ используется старый API:

```python
# ❌ НЕПРАВИЛЬНО - устаревший синтаксис
id = Column(Integer, primary_key=True)  # Не используется!
user = db.query(User).filter(User.id == 1).first()  # Не используется!
```

---

## 📁 Структура проекта

```
example_06/
├── domain/                      # Доменный слой (Core Business)
│   ├── __init__.py
│   ├── models.py               # DAO: SQLAlchemy models с mapped_column
│   └── schemas.py              # DTO: Pydantic schemas для API
│
├── repositories/                # Слой доступа к данным
│   ├── __init__.py
│   ├── base.py                 # Generic CRUD repository
│   └── user_repository.py      # User-specific queries
│
├── services/                    # Бизнес-логика
│   ├── __init__.py
│   └── user_service.py         # Business rules & orchestration
│
├── factories/                   # Паттерн фабрики
│   ├── __init__.py
│   └── user_factory.py         # Entity creation logic
│
├── routers/                     # HTTP endpoints
│   ├── __init__.py
│   └── users.py                # FastAPI routes (thin layer)
│
├── database.py                  # Async DB configuration
├── unit_of_work.py             # Transaction management
├── main.py                     # Application entry point
└── README.md                   # This file
```

---

## 🔍 Разбор слоёв

### 1. Domain Layer (Доменный слой)

#### DAO: `domain/models.py` - SQLAlchemy Models

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    """
    DAO (Data Access Object) - представление таблицы в БД
    ✅ Использует mapped_column и Mapped[type] (SQLAlchemy 2.0)
    """
    __tablename__ = "users"

    # ✅ Modern SQLAlchemy 2.0 syntax
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

#### DTO: `domain/schemas.py` - Pydantic Schemas

```python
from pydantic import BaseModel, EmailStr, ConfigDict

class UserBase(BaseModel):
    """Базовая схема с общими полями"""
    email: EmailStr
    username: str

class UserCreate(UserBase):
    """DTO для создания пользователя (input)"""
    password: str

class UserUpdate(BaseModel):
    """DTO для обновления (все поля optional)"""
    email: EmailStr | None = None
    username: str | None = None
    password: str | None = None

class UserResponse(UserBase):
    """DTO для ответа API (output)"""
    id: int
    is_active: bool
    created_at: datetime

    # ✅ Pydantic v2 syntax
    model_config = ConfigDict(from_attributes=True)
```

**Важно: Schema vs Model**
- **Schema (Pydantic)**: для API (валидация, сериализация)
- **Model (SQLAlchemy)**: для БД (персистентность, queries)

---

### 2. Repository Layer (Доступ к данным)

#### `repositories/user_repository.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from domain.models import User

class UserRepository:
    """
    Инкапсулирует ВСЕ операции с БД
    ✅ Все методы async
    ✅ Использует db.execute() вместо db.query()
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(self, user: User) -> User:
        """Добавить пользователя"""
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get(self, user_id: int) -> User | None:
        """Получить по ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Поиск по email"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Список с пагинацией"""
        result = await self.db.execute(
            select(User).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def update(self, user: User) -> User:
        """Обновить"""
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        """Удалить"""
        await self.db.delete(user)
        await self.db.commit()
```

**Преимущества:**
- ✅ Весь SQL в одном месте
- ✅ Легко менять БД
- ✅ Легко тестировать
- ✅ Переиспользование запросов

---

### 3. Factory Pattern (Создание объектов)

#### `factories/user_factory.py`

```python
from domain.models import User
from domain.schemas import UserCreate

def hash_password(password: str) -> str:
    """Хеширование пароля"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

class UserFactory:
    """
    Централизованное создание User entities
    """

    @staticmethod
    def create_from_schema(user_create: UserCreate) -> User:
        """
        Преобразование DTO → DAO
        Schema (Pydantic) → Model (SQLAlchemy)
        """
        return User(
            email=user_create.email,
            username=user_create.username,
            hashed_password=hash_password(user_create.password)
        )
```

**Зачем нужна фабрика:**
- Централизует логику создания
- Скрывает сложность (например, хеширование)
- Легко тестировать
- Легко изменять правила создания

---

### 4. Unit of Work (Управление транзакциями)

#### `unit_of_work.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.user_repository import UserRepository

class UnitOfWork:
    """
    Координирует репозитории и управляет транзакциями
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.users = UserRepository(db)
        # Добавляйте другие репозитории:
        # self.products = ProductRepository(db)
        # self.orders = OrderRepository(db)

    async def commit(self):
        """Зафиксировать все изменения"""
        await self.db.commit()

    async def rollback(self):
        """Откатить все изменения"""
        await self.db.rollback()
```

**Использование:**
```python
async def create_user_with_profile(user_data, profile_data, db):
    uow = UnitOfWork(db)
    try:
        # Создаём пользователя
        user = await uow.users.add(user_data)
        # Создаём профиль
        profile = await uow.profiles.add(profile_data)
        # Коммитим обе операции вместе
        await uow.commit()
    except:
        # Откатываем обе операции при ошибке
        await uow.rollback()
        raise
```

---

### 5. Service Layer (Бизнес-логика)

#### `services/user_service.py`

```python
from fastapi import HTTPException
from repositories.user_repository import UserRepository
from factories.user_factory import UserFactory
from domain.schemas import UserCreate, UserUpdate

class UserService:
    """
    Содержит бизнес-правила
    ✅ Все методы async
    """

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def create_user(self, user_create: UserCreate) -> User:
        """
        Создание с валидацией бизнес-правил
        """
        # Бизнес-правило: email должен быть уникальным
        existing = await self.repository.get_by_email(user_create.email)
        if existing:
            raise HTTPException(400, "Email уже используется")

        # Используем фабрику для создания
        user = UserFactory.create_from_schema(user_create)

        # Сохраняем через repository
        return await self.repository.add(user)

    async def get_user(self, user_id: int) -> User:
        """Получить с проверкой существования"""
        user = await self.repository.get(user_id)
        if not user:
            raise HTTPException(404, "Пользователь не найден")
        return user

    async def update_user(self, user_id: int, user_update: UserUpdate) -> User:
        """Обновление с валидацией"""
        user = await self.get_user(user_id)

        # Обновляем только переданные поля
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == 'password':
                setattr(user, 'hashed_password', hash_password(value))
            else:
                setattr(user, field, value)

        return await self.repository.update(user)
```

---

### 6. Router Layer (HTTP endpoints)

#### `routers/users.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from domain.schemas import UserCreate, UserUpdate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service)
):
    """
    Роут делает ТОЛЬКО HTTP логику
    Вся бизнес-логика в сервисе
    """
    return await service.create_user(user)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    """Получить пользователя"""
    return await service.get_user(user_id)

@router.get("/", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    repository: UserRepository = Depends(get_repository)
):
    """Список пользователей"""
    return await repository.get_all(skip, limit)
```

---

## 🔄 Поток данных

### Создание пользователя:

```
1. POST /users {"email": "john@example.com", "username": "john", "password": "secret"}
   ↓
2. Router валидирует с UserCreate (Pydantic DTO)
   ↓
3. Service проверяет бизнес-правила (уникальность email)
   ↓
4. Factory создаёт User entity (SQLAlchemy DAO)
   ↓
5. Repository сохраняет в БД через await db.execute()
   ↓
6. UnitOfWork коммитит транзакцию
   ↓
7. Service возвращает User (DAO)
   ↓
8. Router преобразует в UserResponse (DTO)
   ↓
9. HTTP Response: 201 Created with user data
```

---

## 🚀 Как запустить

```bash
cd examples/example_06
pip install fastapi uvicorn sqlalchemy aiosqlite pydantic[email]

python main.py
# или
uvicorn main:app --reload
```

Документация:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 📝 Примеры запросов

### Create User
```bash
curl -X POST "http://localhost:8000/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "username": "johndoe",
    "password": "SecurePassword123"
  }'
```

### Get User
```bash
curl "http://localhost:8000/users/1"
```

### List Users
```bash
curl "http://localhost:8000/users/?skip=0&limit=10"
```

### Update User
```bash
curl -X PATCH "http://localhost:8000/users/1" \
  -H "Content-Type: application/json" \
  -d '{"username": "john_updated"}'
```

---

## 🎯 Преимущества DDD

1. **Separation of Concerns** / Разделение ответственности
   - Каждый слой делает свою работу
   - Легко найти и изменить код

2. **Testability** / Тестируемость
   - Каждый слой тестируется отдельно
   - Легко мокировать зависимости

3. **Maintainability** / Поддерживаемость
   - Изменения локализованы
   - Понятная структура

4. **Scalability** / Масштабируемость
   - Легко добавлять новые сущности
   - Паттерны переиспользуются

5. **Flexibility** / Гибкость
   - Легко менять БД (только repository)
   - Легко менять API (только router)

---

## 📚 Ключевые паттерны

- **Repository**: Абстракция доступа к данным
- **Unit of Work**: Управление транзакциями
- **Service Layer**: Бизнес-логика
- **Factory**: Создание объектов
- **DTO**: Передача данных между слоями
- **DAO**: Представление таблиц БД

---

## 🐛 Частые ошибки

### 1. Путаете Schema и Model

```python
# ❌ НЕПРАВИЛЬНО
@router.post("/users")
async def create(user: User):  # User - это DAO!
    pass

# ✅ ПРАВИЛЬНО
@router.post("/users")
async def create(user: UserCreate):  # UserCreate - это DTO!
    pass
```

### 2. Используете старый SQLAlchemy API

```python
# ❌ НЕПРАВИЛЬНО
id = Column(Integer, primary_key=True)
user = db.query(User).first()

# ✅ ПРАВИЛЬНО
id: Mapped[int] = mapped_column(Integer, primary_key=True)
result = await db.execute(select(User))
user = result.scalar_one_or_none()
```

### 3. Забываете async/await

```python
# ❌ НЕПРАВИЛЬНО
def get_user(user_id: int):
    return repository.get(user_id)  # Нет await!

# ✅ ПРАВИЛЬНО
async def get_user(user_id: int):
    return await repository.get(user_id)
```

---

## 📝 Задания для практики

1. ✏️ Добавьте `Product` entity со всеми слоями
2. ✏️ Реализуйте `Order` с связями many-to-many
3. ✏️ Добавьте аутентификацию (JWT tokens)
4. ✏️ Реализуйте soft delete (is_deleted flag)
5. ✏️ Добавьте event sourcing для аудита

---

## 🔗 Полезные ссылки

- [Domain-Driven Design (Eric Evans)](https://www.domainlanguage.com/ddd/)
- [Clean Architecture (Robert Martin)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/advanced/)

---

**Это production-ready архитектура для серьёзных приложений! 🚀**
