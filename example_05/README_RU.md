# Example 05: Dependency Injection в FastAPI
# Advanced DI Patterns with Async SQLAlchemy 2.0

**[🇬🇧 English version](README.md)**

## 📚 Что изучаем

В этом примере подробно разбираем Dependency Injection:
- ✅ Что такое DI и зачем он нужен
- ✅ Как работает `Depends()` внутри
- ✅ **Repository Pattern** с async SQLAlchemy 2.0
- ✅ **Service Layer** для бизнес-логики
- ✅ Цепочки зависимостей (nested dependencies)
- ✅ Классы как зависимости
- ✅ **Все операции асинхронные** (async/await)
- ✅ **Используем `db.execute()` и `mapped_column`**
- ✅ Тестирование с dependency override

## 🎯 Что такое Dependency Injection?

**Dependency Injection (DI)** - паттерн проектирования, при котором зависимости объекта предоставляются извне, а не создаются внутри.

### ❌ Без DI (плохо):

```python
@app.get("/users")
async def get_users():
    # Роут создаёт зависимость сам
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(User))
            users = result.scalars().all()
            return users
        finally:
            await db.close()

    # Проблемы:
    # 1. Код повторяется в каждом роуте
    # 2. Сложно тестировать (нельзя подменить db)
    # 3. Легко забыть закрыть соединение
    # 4. Нарушение принципа единственной ответственности
```

### ✅ С DI (хорошо):

```python
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    # FastAPI автоматически инжектирует зависимость
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users

    # Преимущества:
    # 1. Нет дублирования кода
    # 2. Легко тестировать (мокаем get_db)
    # 3. Гарантированное закрытие соединения
    # 4. Чистый и читаемый код
```

---

## 🚀 Как запустить

```bash
# Установить зависимости
pip install fastapi uvicorn sqlalchemy aiosqlite pydantic[email]

# Запустить сервер
cd example_05
python main.py
# или
uvicorn main:app --reload
```

База данных: `example_05.db` (создаётся автоматически)

Документация: `http://localhost:8000/docs`

---

## ⚡ SQLAlchemy 2.0 - Современный подход

### ✅ Этот пример использует ТОЛЬКО новый API:

```python
# ✅ Async engine
engine = create_async_engine("sqlite+aiosqlite:///./example_05.db")

# ✅ Async session
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession)

# ✅ Modern ORM с mapped_column
class User(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)

# ✅ Новый query API
result = await db.execute(select(User).where(User.id == user_id))
user = result.scalar_one_or_none()

```

---

## 🏗️ Архитектура слоев

### Dependency Chain:

```
HTTP Request
    ↓
Router (HTTP layer)
    ↓ Depends(get_user_service)
UserService (Business logic)
    ↓ Depends(get_user_repository)
UserRepository (Data access)
    ↓ Depends(get_db)
AsyncSession (Database)
```

### Преимущества многослойной архитектуры:

1. **Разделение ответственности:**
   - Router: HTTP запросы/ответы
   - Service: Бизнес-правила
   - Repository: Доступ к данным

2. **Тестируемость:**
   - Каждый слой тестируется отдельно
   - Легко мокировать зависимости

3. **Переиспользование:**
   - Service можно использовать в разных роутах
   - Repository в разных сервисах

---

## 🔍 Разбор паттернов

### 1. Database Dependency (Базовая зависимость)

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from typing import AsyncGenerator

# Async engine
engine = create_async_engine(
    "sqlite+aiosqlite:///./example_05.db",
    echo=True  # SQL логирование
)

# Async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# ✅ Dependency функция
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Создаёт async сессию БД и гарантирует её закрытие
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session  # Передаём в роут
        finally:
            await session.close()  # Всегда закрываем
```

**Как работает:**
1. FastAPI видит `Depends(get_db)`
2. Вызывает `get_db()`
3. Получает session из `yield`
4. Передаёт в параметр функции
5. После выполнения выполняет `finally`

---

### 2. Repository Pattern (Слой доступа к данным)

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

class UserRepository:
    """
    Инкапсулирует всю логику доступа к данным о пользователях
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> User | None:
        """✅ Используем новый API: execute + select"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """Поиск по username"""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def list_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Список с пагинацией"""
        result = await self.db.execute(
            select(User)
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        return result.scalars().all()

    async def create(self, user_data: dict) -> User:
        """Создание пользователя"""
        db_user = User(**user_data)
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def update(self, user: User, update_data: dict) -> User:
        """Обновление"""
        for field, value in update_data.items():
            setattr(user, field, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        """Удаление"""
        await self.db.delete(user)
        await self.db.commit()
```

**Dependency для repository:**
```python
def get_user_repository(
    db: AsyncSession = Depends(get_db)
) -> UserRepository:
    """
    Создаёт repository с инжектированной сессией БД
    """
    return UserRepository(db)
```

**Преимущества Repository:**
- ✅ Весь SQL в одном месте
- ✅ Легко менять БД (только repository)
- ✅ Легко тестировать (mock repository)
- ✅ Переиспользование запросов

---

### 3. Service Layer (Бизнес-логика)

```python
from fastapi import HTTPException

class UserService:
    """
    Содержит бизнес-логику работы с пользователями
    """

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def get_user(self, user_id: int) -> User:
        """Получить пользователя с проверкой существования"""
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(404, "Пользователь не найден")
        return user

    async def create_user(self, username: str, email: str, password: str) -> User:
        """Создание с валидацией уникальности"""
        # Бизнес-правило: username должен быть уникальным
        existing = await self.repository.get_by_username(username)
        if existing:
            raise HTTPException(400, "Username уже занят")

        # Бизнес-правило: хешируем пароль
        hashed = hash_password(password)

        user_data = {
            "username": username,
            "email": email,
            "hashed_password": hashed
        }

        return await self.repository.create(user_data)

    async def update_user(self, user_id: int, update_data: dict) -> User:
        """Обновление с валидацией"""
        user = await self.get_user(user_id)

        # Бизнес-правило: нельзя изменить на занятый username
        if "username" in update_data:
            existing = await self.repository.get_by_username(update_data["username"])
            if existing and existing.id != user_id:
                raise HTTPException(400, "Username уже занят")

        return await self.repository.update(user, update_data)

    async def delete_user(self, user_id: int) -> None:
        """Удаление с проверкой"""
        user = await self.get_user(user_id)
        await self.repository.delete(user)
```

**Dependency для service:**
```python
def get_user_service(
    repository: UserRepository = Depends(get_user_repository)
) -> UserService:
    """
    Создаёт сервис с инжектированным repository
    """
    return UserService(repository)
```

**Преимущества Service:**
- ✅ Вся бизнес-логика в одном месте
- ✅ Переиспользование в разных роутах
- ✅ Легко тестировать
- ✅ Чистый код в роутах

---

### 4. Router Layer (HTTP endpoints)

```python
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service)
):
    """
    Роут делает ТОЛЬКО HTTP логику:
    - Валидация входных данных (Pydantic)
    - Вызов сервиса
    - Формирование ответа
    """
    db_user = await service.create_user(
        username=user.username,
        email=user.email,
        password=user.password
    )
    return db_user

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    """Роут только вызывает сервис"""
    return await service.get_user(user_id)

@router.get("/", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    repository: UserRepository = Depends(get_user_repository)
):
    """Простые операции могут использовать repository напрямую"""
    return await repository.list_users(skip, limit)
```

**Обратите внимание:**
- ✅ Роуты тонкие - только HTTP логика
- ✅ Вся бизнес-логика в сервисе
- ✅ Все операции async
- ✅ Dependency injection на всех уровнях

---

## 🔄 Цепочки зависимостей

### Как FastAPI разрешает зависимости:

```python
@router.post("/users")
async def create(
    user: UserCreate,
    service: UserService = Depends(get_user_service)
):
    ...

# FastAPI выполняет:
# 1. db = await get_db()
# 2. repository = get_user_repository(db)
# 3. service = get_user_service(repository)
# 4. create(user, service)
# 5. await db.close() (в finally)
```

**Граф зависимостей:**
```
create_user
    ↓
get_user_service
    ↓
get_user_repository
    ↓
get_db
    ↓
AsyncSession
```

**Кэширование:**
FastAPI кэширует зависимости в рамках одного запроса:

```python
@router.get("/demo")
async def demo(
    db1: AsyncSession = Depends(get_db),
    db2: AsyncSession = Depends(get_db)
):
    # get_db() вызовется только ОДИН раз
    # db1 и db2 - это ОДИН И ТОТ ЖЕ объект
    assert db1 is db2  # True!
```

---

## 🧪 Тестирование

### Override Dependencies для тестов:

```python
from fastapi.testclient import TestClient

# Mock repository
class MockUserRepository:
    async def get_by_id(self, user_id: int):
        return User(id=user_id, username="test")

def get_mock_repository():
    return MockUserRepository()

# Override в тестах
app.dependency_overrides[get_user_repository] = get_mock_repository

# Теперь все роуты используют mock!
client = TestClient(app)
response = client.get("/users/1")
assert response.json()["username"] == "test"

# Очистка
app.dependency_overrides.clear()
```

См. `test_di.py` для полных примеров тестов.

---

## 📝 Задания для практики

1. ✏️ Добавьте `ProductRepository` и `ProductService` для товаров
2. ✏️ Реализуйте аутентификацию через DI (JWT токены)
3. ✏️ Создайте `AuditLogger` сервис для логирования действий
4. ✏️ Добавьте `CacheService` для кэширования запросов
5. ✏️ Реализуйте `RateLimiter` dependency для ограничения запросов

---

## 🐛 Частые ошибки

### 1. Используете старый query API

```python
# ❌ НЕПРАВИЛЬНО (SQLAlchemy 1.x)
user = db.query(User).filter(User.id == user_id).first()

# ✅ ПРАВИЛЬНО (SQLAlchemy 2.0)
result = await db.execute(select(User).where(User.id == user_id))
user = result.scalar_one_or_none()
```

### 2. Забыли async/await

```python
# ❌ НЕПРАВИЛЬНО
def get_user(db: AsyncSession = Depends(get_db)):
    result = db.execute(select(User))  # Нет await!
    return result.scalars().all()

# ✅ ПРАВИЛЬНО
async def get_user(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()
```

### 3. Забыли скобки в Depends

```python
# ❌ НЕПРАВИЛЬНО
def route(db = Depends):
    pass

# ✅ ПРАВИЛЬНО
def route(db: AsyncSession = Depends(get_db)):
    pass
```

### 4. Используете Column вместо mapped_column

```python
# ❌ НЕПРАВИЛЬНО
id = Column(Integer, primary_key=True)

# ✅ ПРАВИЛЬНО
id: Mapped[int] = mapped_column(Integer, primary_key=True)
```

---

## 🎯 Ключевые концепции

### Преимущества DI:

1. ✅ **Чистый код**: нет дублирования
2. ✅ **Тестируемость**: легко мокировать
3. ✅ **Поддерживаемость**: изменения локализованы
4. ✅ **Гибкость**: легко менять реализации

### Async/Await обязательно:

```python
# ✅ Все примеры используют
async def func(db: AsyncSession = Depends(get_db)):
    result = await db.execute(...)
    return result.scalars().all()
```

### SQLAlchemy 2.0 обязательно:

```python
# ✅ mapped_column + Mapped
id: Mapped[int] = mapped_column(Integer, primary_key=True)

# ✅ execute + select
result = await db.execute(select(User))

# ❌ НЕ используется
id = Column(Integer, primary_key=True)
users = db.query(User).all()
```

---

## 🔗 Следующий шаг

Переходите к **Example 06**, где применим все знания для создания полноценного **Domain-Driven Design** приложения!

**Что вас ждёт:**
- Полная DDD архитектура
- DAO, DTO, Repositories, Services, Factories, UnitOfWork
- 100% async код
- SQLAlchemy 2.0
- Production-ready паттерны

---

**Важно**: Этот пример - фундамент для понимания профессиональной разработки на FastAPI!
