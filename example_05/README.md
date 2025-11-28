# Example 05: Dependency Injection in FastAPI
# Advanced DI Patterns with Async SQLAlchemy 2.0

**[🇷🇺 Русская версия](README_RU.md)**

## 📚 What You'll Learn

In this example, we cover Dependency Injection in detail:
- ✅ What DI is and why it's needed
- ✅ How `Depends()` works internally
- ✅ **Repository Pattern** with async SQLAlchemy 2.0
- ✅ **Service Layer** for business logic
- ✅ Dependency chains (nested dependencies)
- ✅ Classes as dependencies
- ✅ **All operations are asynchronous** (async/await)
- ✅ **Using `db.execute()` and `mapped_column`**
- ✅ Testing with dependency override

## 🎯 What is Dependency Injection?

**Dependency Injection (DI)** - a design pattern where an object's dependencies are provided from outside rather than created internally.

### ❌ Without DI (bad):

```python
@app.get("/users")
async def get_users():
    # Route creates dependency itself
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(User))
            users = result.scalars().all()
            return users
        finally:
            await db.close()

    # Problems:
    # 1. Code repeats in every route
    # 2. Hard to test (can't mock db)
    # 3. Easy to forget closing connection
    # 4. Violates single responsibility principle
```

### ✅ With DI (good):

```python
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    # FastAPI automatically injects dependency
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users

    # Benefits:
    # 1. No code duplication
    # 2. Easy to test (mock get_db)
    # 3. Guaranteed connection closure
    # 4. Clean and readable code
```

---

## 🚀 How to Run

```bash
# Install dependencies
pip install fastapi uvicorn sqlalchemy aiosqlite pydantic[email]

# Run server
cd example_05
python main.py
# or
uvicorn main:app --reload
```

Database: `example_05.db` (created automatically)

Documentation: `http://localhost:8000/docs`

---

## ⚡ SQLAlchemy 2.0 - Modern Approach

### ✅ This example uses ONLY the new API:

```python
# ✅ Async engine
engine = create_async_engine("sqlite+aiosqlite:///./example_05.db")

# ✅ Async session
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession)

# ✅ Modern ORM with mapped_column
class User(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)

# ✅ New query API
result = await db.execute(select(User).where(User.id == user_id))
user = result.scalar_one_or_none()

```

---

## 🏗️ Layer Architecture

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

### Benefits of multi-layer architecture:

1. **Separation of concerns:**
   - Router: HTTP requests/responses
   - Service: Business rules
   - Repository: Data access

2. **Testability:**
   - Each layer is tested separately
   - Easy to mock dependencies

3. **Reusability:**
   - Service can be used in different routes
   - Repository in different services

---

## 🔍 Pattern Breakdown

### 1. Database Dependency (Base dependency)

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from typing import AsyncGenerator

# Async engine
engine = create_async_engine(
    "sqlite+aiosqlite:///./example_05.db",
    echo=True  # SQL logging
)

# Async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# ✅ Dependency function
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Creates async DB session and guarantees its closure
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session  # Pass to route
        finally:
            await session.close()  # Always close
```

**How it works:**
1. FastAPI sees `Depends(get_db)`
2. Calls `get_db()`
3. Gets session from `yield`
4. Passes to function parameter
5. After execution runs `finally`

---

### 2. Repository Pattern (Data access layer)

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

class UserRepository:
    """
    Encapsulates all data access logic for users
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> User | None:
        """✅ Using new API: execute + select"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """Search by username"""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def list_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """List with pagination"""
        result = await self.db.execute(
            select(User)
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        return result.scalars().all()

    async def create(self, user_data: dict) -> User:
        """Create user"""
        db_user = User(**user_data)
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def update(self, user: User, update_data: dict) -> User:
        """Update"""
        for field, value in update_data.items():
            setattr(user, field, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        """Delete"""
        await self.db.delete(user)
        await self.db.commit()
```

**Dependency for repository:**
```python
def get_user_repository(
    db: AsyncSession = Depends(get_db)
) -> UserRepository:
    """
    Creates repository with injected DB session
    """
    return UserRepository(db)
```

**Repository benefits:**
- ✅ All SQL in one place
- ✅ Easy to change DB (only repository)
- ✅ Easy to test (mock repository)
- ✅ Query reusability

---

### 3. Service Layer (Business logic)

```python
from fastapi import HTTPException

class UserService:
    """
    Contains business logic for working with users
    """

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def get_user(self, user_id: int) -> User:
        """Get user with existence check"""
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(404, "User not found")
        return user

    async def create_user(self, username: str, email: str, password: str) -> User:
        """Create with uniqueness validation"""
        # Business rule: username must be unique
        existing = await self.repository.get_by_username(username)
        if existing:
            raise HTTPException(400, "Username already taken")

        # Business rule: hash password
        hashed = hash_password(password)

        user_data = {
            "username": username,
            "email": email,
            "hashed_password": hashed
        }

        return await self.repository.create(user_data)

    async def update_user(self, user_id: int, update_data: dict) -> User:
        """Update with validation"""
        user = await self.get_user(user_id)

        # Business rule: can't change to taken username
        if "username" in update_data:
            existing = await self.repository.get_by_username(update_data["username"])
            if existing and existing.id != user_id:
                raise HTTPException(400, "Username already taken")

        return await self.repository.update(user, update_data)

    async def delete_user(self, user_id: int) -> None:
        """Delete with check"""
        user = await self.get_user(user_id)
        await self.repository.delete(user)
```

**Dependency for service:**
```python
def get_user_service(
    repository: UserRepository = Depends(get_user_repository)
) -> UserService:
    """
    Creates service with injected repository
    """
    return UserService(repository)
```

**Service benefits:**
- ✅ All business logic in one place
- ✅ Reusability in different routes
- ✅ Easy to test
- ✅ Clean code in routes

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
    Route does ONLY HTTP logic:
    - Input data validation (Pydantic)
    - Service call
    - Response formatting
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
    """Route only calls service"""
    return await service.get_user(user_id)

@router.get("/", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    repository: UserRepository = Depends(get_user_repository)
):
    """Simple operations can use repository directly"""
    return await repository.list_users(skip, limit)
```

**Note:**
- ✅ Routes are thin - only HTTP logic
- ✅ All business logic in service
- ✅ All operations async
- ✅ Dependency injection at all levels

---

## 🔄 Dependency Chains

### How FastAPI resolves dependencies:

```python
@router.post("/users")
async def create(
    user: UserCreate,
    service: UserService = Depends(get_user_service)
):
    ...

# FastAPI executes:
# 1. db = await get_db()
# 2. repository = get_user_repository(db)
# 3. service = get_user_service(repository)
# 4. create(user, service)
# 5. await db.close() (in finally)
```

**Dependency graph:**
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

**Caching:**
FastAPI caches dependencies within a single request:

```python
@router.get("/demo")
async def demo(
    db1: AsyncSession = Depends(get_db),
    db2: AsyncSession = Depends(get_db)
):
    # get_db() will be called only ONCE
    # db1 and db2 are the SAME object
    assert db1 is db2  # True!
```

---

## 🧪 Testing

### Override Dependencies for tests:

```python
from fastapi.testclient import TestClient

# Mock repository
class MockUserRepository:
    async def get_by_id(self, user_id: int):
        return User(id=user_id, username="test")

def get_mock_repository():
    return MockUserRepository()

# Override in tests
app.dependency_overrides[get_user_repository] = get_mock_repository

# Now all routes use mock!
client = TestClient(app)
response = client.get("/users/1")
assert response.json()["username"] == "test"

# Cleanup
app.dependency_overrides.clear()
```

See `test_di.py` for full test examples.

---

## 📝 Practice Tasks

1. ✏️ Add `ProductRepository` and `ProductService` for products
2. ✏️ Implement authentication via DI (JWT tokens)
3. ✏️ Create `AuditLogger` service for action logging
4. ✏️ Add `CacheService` for request caching
5. ✏️ Implement `RateLimiter` dependency for request limiting

---

## 🐛 Common Mistakes

### 1. Using old query API

```python
# ❌ WRONG (SQLAlchemy 1.x)
user = db.query(User).filter(User.id == user_id).first()

# ✅ CORRECT (SQLAlchemy 2.0)
result = await db.execute(select(User).where(User.id == user_id))
user = result.scalar_one_or_none()
```

### 2. Forgot async/await

```python
# ❌ WRONG
def get_user(db: AsyncSession = Depends(get_db)):
    result = db.execute(select(User))  # No await!
    return result.scalars().all()

# ✅ CORRECT
async def get_user(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()
```

### 3. Forgot parentheses in Depends

```python
# ❌ WRONG
def route(db = Depends):
    pass

# ✅ CORRECT
def route(db: AsyncSession = Depends(get_db)):
    pass
```

### 4. Using Column instead of mapped_column

```python
# ❌ WRONG
id = Column(Integer, primary_key=True)

# ✅ CORRECT
id: Mapped[int] = mapped_column(Integer, primary_key=True)
```

---

## 🎯 Key Concepts

### DI Benefits:

1. ✅ **Clean code**: no duplication
2. ✅ **Testability**: easy to mock
3. ✅ **Maintainability**: changes are localized
4. ✅ **Flexibility**: easy to change implementations

### Async/Await is mandatory:

```python
# ✅ All examples use
async def func(db: AsyncSession = Depends(get_db)):
    result = await db.execute(...)
    return result.scalars().all()
```

### SQLAlchemy 2.0 is mandatory:

```python
# ✅ mapped_column + Mapped
id: Mapped[int] = mapped_column(Integer, primary_key=True)

# ✅ execute + select
result = await db.execute(select(User))

# ❌ NOT used
id = Column(Integer, primary_key=True)
users = db.query(User).all()
```

---

## 🔗 Next Steps

Move on to **Example 06**, where we'll apply all knowledge to create a full-featured **Domain-Driven Design** application!

**What awaits you:**
- Full DDD architecture
- DAO, DTO, Repositories, Services, Factories, UnitOfWork
- 100% async code
- SQLAlchemy 2.0
- Production-ready patterns

---

**Important**: This example is the foundation for understanding professional FastAPI development!
