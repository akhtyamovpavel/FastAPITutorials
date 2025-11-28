# Пример 03: Асинхронная работа с базой данных

**[🇬🇧 English version](README.md)**

---

## 📚 Что изучаем

В этом примере разбираем современную работу с БД:
- ✅ **Async SQLAlchemy 2.0** (все операции асинхронные!)
- ✅ **`db.execute(select(...))` вместо `db.query()`** - новый API
- ✅ **`mapped_column` и `Mapped[type]` вместо `Column`** - современный ORM
- ✅ **Schema (Pydantic) vs Model (SQLAlchemy)** - ключевое различие!
- ✅ CRUD операции (Create, Read, Update, Delete)
- ✅ Dependency Injection через `Depends(get_db)`
- ✅ Управление async сессиями
- ✅ **Все примеры в ОДНОМ файле** (main.py)

## 🎯 КРИТИЧЕСКИ ВАЖНО: Schema vs Model

### ❌ Частая ошибка начинающих:
```python
@app.post("/users")
async def create_user(user: UserModel):  # НЕПРАВИЛЬНО!
    # UserModel - это SQLAlchemy ORM модель для БД
    # Нельзя использовать для API!
    pass
```

### ✅ Правильный подход:

```python
# Schema (Pydantic) - для API
class UserCreate(BaseModel):
    """Что принимаем от клиента через API"""
    email: EmailStr
    username: str
    password: str

# Model (SQLAlchemy) - для БД
class User(Base):
    """Как хранится в базе данных"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str] = mapped_column(String)

@app.post("/users")
async def create_user(
    user: UserCreate,              # Schema для валидации
    db: AsyncSession = Depends(get_db)
):
    # Преобразуем Schema → Model
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hash_password(user.password)
    )
    db.add(db_user)
    await db.commit()
    return db_user
```

---

## 📊 Таблица различий

| Аспект | Schema (Pydantic) | Model (SQLAlchemy) |
|--------|-------------------|-------------------|
| **Назначение** | API валидация и сериализация | Таблица в БД |
| **Где живёт** | Application layer | Database layer |
| **Наследуется от** | `BaseModel` | `Base` |
| **Типы полей** | Python типы (`str`, `int`) | SQL типы (`String`, `Integer`) |
| **Валидация** | Входные/выходные данные API | Структура таблицы |
| **Примеры** | `UserCreate`, `UserResponse` | `User`, `Product` |

### Зачем нужны оба?

1. **Безопасность**: скрываем служебные поля (пароли, токены)
2. **Гибкость**: API может отличаться от БД
3. **Множественность**: одна модель БД → много API схем
4. **Разделение ответственности**: API не знает о БД

### Пример workflow:

```
Клиент → JSON → UserCreate (Schema) → валидация
                                ↓
                        User (Model) → БД
                                ↓
                  UserResponse (Schema) ← сериализация
                                ↓
                        JSON → Клиент
```

---

## 🚀 Как запустить

```bash
# Установить зависимости
pip install fastapi uvicorn sqlalchemy aiosqlite pydantic[email]

# Запустить сервер
cd example_03
uvicorn main:app --reload
```

База данных создастся автоматически: `example_03.db`

Документация: `http://localhost:8000/docs`

---

## ⚡ SQLAlchemy 2.0: Старый vs Новый API

### ❌ СТАРЫЙ СПОСОБ (SQLAlchemy 1.x - НЕ используется!)

```python
# Синхронный Session
from sqlalchemy.orm import Session

class User(Base):
    __tablename__ = "users"

    # Старый Column без типов
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

def get_user(db: Session, user_id: int):
    # Старый query API
    user = db.query(User).filter(User.id == user_id).first()
    return user

@app.get("/users/{user_id}")
def get(user_id: int, db: Session = Depends(get_db)):
    # Синхронный код - блокирует сервер!
    return get_user(db, user_id)
```

### ✅ НОВЫЙ СПОСОБ (SQLAlchemy 2.0 - используется в примере!)

```python
# Async AsyncSession
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import select

class User(Base):
    __tablename__ = "users"

    # Новый mapped_column с Mapped типами
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

async def get_user(db: AsyncSession, user_id: int):
    # Новый execute + select API
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    return user

@app.get("/users/{user_id}")
async def get(user_id: int, db: AsyncSession = Depends(get_db)):
    # Async код - не блокирует!
    return await get_user(db, user_id)
```

---

## 🔄 Миграция паттернов

### 1. Model Definition

```python
# ❌ СТАРОЕ (Column)
class User(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True)

# ✅ НОВОЕ (mapped_column + Mapped)
class User(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True)
```

### 2. Query Execution

```python
# ❌ СТАРОЕ (query)
users = db.query(User).filter(User.age > 18).all()

# ✅ НОВОЕ (execute + select)
result = await db.execute(
    select(User).where(User.age > 18)
)
users = result.scalars().all()
```

### 3. Get Single Record

```python
# ❌ СТАРОЕ (.first())
user = db.query(User).filter(User.id == 1).first()

# ✅ НОВОЕ (scalar_one_or_none)
result = await db.execute(
    select(User).where(User.id == 1)
)
user = result.scalar_one_or_none()
```

### 4. Count Records

```python
# ❌ СТАРОЕ (.count())
count = db.query(User).count()

# ✅ НОВОЕ (func.count)
from sqlalchemy import func
result = await db.execute(
    select(func.count()).select_from(User)
)
count = result.scalar()
```

---

## 🔍 Разбор компонентов

### 1. Async Database Setup

```python
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)

engine = create_async_engine(
    "sqlite+aiosqlite:///./example_03.db",
    echo=True  # Логирование SQL запросов
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

**Важно:**
- `create_async_engine` вместо `create_engine`
- `async_sessionmaker` вместо `sessionmaker`
- `AsyncSession` вместо `Session`
- `yield` для передачи сессии
- `await session.close()` для корректного закрытия

---

### 2. Modern ORM Model

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, DateTime
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    # ✅ Mapped типы для лучшей поддержки IDE
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

**Преимущества Mapped:**
- IDE автодополнение работает идеально
- Ловит ошибки типов на этапе разработки
- Чище и понятнее код
- Соответствует SQLAlchemy 2.0 best practices

---

### 3. Pydantic Schemas (DTOs)

```python
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

# Базовая схема
class UserBase(BaseModel):
    email: EmailStr
    username: str

# Для создания (input)
class UserCreate(UserBase):
    password: str  # Принимаем plain password

# Для обновления (input)
class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = None
    password: str | None = None

# Для ответа API (output)
class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    # ✅ Pydantic v2 - from_attributes вместо orm_mode
    model_config = ConfigDict(from_attributes=True)
```

**Важно (Pydantic v2):**
- `from_attributes=True` заменяет старый `orm_mode=True`
- `model_config = ConfigDict()` заменяет `class Config`
- Позволяет создавать схемы из ORM моделей:
  ```python
  user_response = UserResponse.from_orm(db_user)
  ```

---

### 4. CRUD Operations - Современный стиль

#### CREATE

```python
@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    # Проверка уникальности email
    result = await db.execute(
        select(User).where(User.email == user.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(400, "Email уже используется")

    # Schema → Model
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hash_password(user.password)  # Хешируем!
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user
```

#### READ (list)

```python
@app.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    # ✅ Новый стиль: select + execute + scalars
    result = await db.execute(
        select(User)
        .offset(skip)
        .limit(limit)
        .order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    return users
```

#### READ (single)

```python
@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(404, "Пользователь не найден")

    return user
```

#### UPDATE

```python
@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    # Найти в БД
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(404, "Не найдено")

    # Обновить только переданные поля
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == 'password':
            setattr(db_user, 'hashed_password', hash_password(value))
        else:
            setattr(db_user, field, value)

    await db.commit()
    await db.refresh(db_user)

    return db_user
```

#### DELETE

```python
@app.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(404, "Не найдено")

    await db.delete(db_user)
    await db.commit()

    return None  # 204 No Content
```

---

## 📋 Методы Result Object

```python
result = await db.execute(select(User))

# Получить один скаляр (одно значение)
user = result.scalar_one()          # ❌ Ошибка если нет или > 1
user = result.scalar_one_or_none()  # ✅ None если нет
user = result.scalar()              # ✅ None если нет, первый если > 1

# Получить несколько скаляров
users = result.scalars().all()      # ✅ Список объектов User

# Получить Row (кортеж)
row = result.one()                  # ❌ Ошибка если нет или > 1
rows = result.all()                 # ✅ Список кортежей
```

---

## 🎯 Лучшие практики

### 1. Всегда используйте async/await

```python
# ✅ ПРАВИЛЬНО
@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()

# ❌ НЕПРАВИЛЬНО
@app.get("/users")
def get_users(db: AsyncSession = Depends(get_db)):
    # Нет async - не работает!
    result = db.execute(select(User))
    return result.scalars().all()
```

### 2. Используйте mapped_column и Mapped

```python
# ✅ ПРАВИЛЬНО (SQLAlchemy 2.0)
class User(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)

# ❌ НЕПРАВИЛЬНО (устаревший синтаксис)
class User(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String)
```

### 3. Разделяйте Schema и Model

```python
# ✅ ПРАВИЛЬНО
UserCreate, UserUpdate, UserResponse - для API (Pydantic)
User - для БД (SQLAlchemy)

# ❌ НЕПРАВИЛЬНО
Одна модель для всего
```

### 4. Используйте Depends(get_db)

```python
# ✅ ПРАВИЛЬНО
async def my_route(db: AsyncSession = Depends(get_db)):
    # Сессия автоматически закроется
    pass

# ❌ НЕПРАВИЛЬНО
async def my_route():
    async with AsyncSessionLocal() as db:
        # Дублирование кода
        pass
```

---

## 📝 Задания для практики

1. ✏️ Добавьте таблицу `posts` со связью many-to-one к `users`
2. ✏️ Реализуйте soft delete (поле `deleted_at`)
3. ✏️ Добавьте полнотекстовый поиск пользователей
4. ✏️ Создайте endpoint для bulk insert пользователей
5. ✏️ Добавьте пагинацию с метаданными (total_count, pages)

---

## 🐛 Частые ошибки

### 1. Используете старый .query() API

```python
# ❌ НЕПРАВИЛЬНО (SQLAlchemy 1.x)
users = db.query(User).all()

# ✅ ПРАВИЛЬНО (SQLAlchemy 2.0)
result = await db.execute(select(User))
users = result.scalars().all()
```

### 2. Забыли await

```python
# ❌ НЕПРАВИЛЬНО
result = db.execute(select(User))  # Нет await!

# ✅ ПРАВИЛЬНО
result = await db.execute(select(User))
```

### 3. Используете Column вместо mapped_column

```python
# ❌ НЕПРАВИЛЬНО
id = Column(Integer, primary_key=True)

# ✅ ПРАВИЛЬНО
id: Mapped[int] = mapped_column(Integer, primary_key=True)
```

### 4. Путаете Schema и Model

```python
# ❌ НЕПРАВИЛЬНО
@app.post("/users")
async def create(user: User):  # User - это SQLAlchemy модель!
    pass

# ✅ ПРАВИЛЬНО
@app.post("/users")
async def create(user: UserCreate):  # UserCreate - Pydantic схема
    pass
```

---

## 🔗 Следующий шаг

Переходите к **Example 04**, где подробно изучим **Dependency Injection** и паттерн **Service Layer**!

**Что вы узнаете:**
- Как работает `Depends()` внутри
- Repository pattern
- Service layer для бизнес-логики
- Цепочки зависимостей
