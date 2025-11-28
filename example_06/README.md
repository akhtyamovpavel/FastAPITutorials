# Example 06: Full Domain-Driven Design (DDD)

**[🇷🇺 Русская версия](README_RU.md)**

## 📚 What You'll Learn

Full production-ready architecture:
- ✅ **100% Async code** (all operations asynchronous!)
- ✅ **SQLAlchemy 2.0** with `db.execute()` and `mapped_column`
- ✅ **DAO** (Data Access Objects) - SQLAlchemy models
- ✅ **DTO** (Data Transfer Objects) - Pydantic schemas
- ✅ **Repositories** - data access abstraction
- ✅ **Services** - business logic
- ✅ **Factories** - object creation
- ✅ **UnitOfWork** - transaction management
- ✅ **Routers** - thin HTTP layer
- ✅ **Clean Architecture** principles

## 🏗️ Architecture Layers

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

## 🎯 CRITICAL: All Operations are Async!

### ✅ This example uses ONLY async:

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

### ❌ Synchronous code is NOT used:

```python
# ❌ WRONG - NOT used in this example!
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

engine = create_engine("sqlite:///./db.db")  # Sync!
db = Session(engine)  # Sync!
user = db.query(User).first()  # Sync!
```

---

## ⚡ SQLAlchemy 2.0 - Modern API

### ✅ ONLY new syntax is used:

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

### ❌ Old API is NOT used:

```python
# ❌ WRONG - deprecated syntax
id = Column(Integer, primary_key=True)  # Not used!
user = db.query(User).filter(User.id == 1).first()  # Not used!
```

---

## 📁 Project Structure

```
example_06/
├── domain/                      # Domain layer (Core Business)
│   ├── __init__.py
│   ├── models.py               # DAO: SQLAlchemy models with mapped_column
│   └── schemas.py              # DTO: Pydantic schemas for API
│
├── repositories/                # Data access layer
│   ├── __init__.py
│   ├── base.py                 # Generic CRUD repository
│   └── user_repository.py      # User-specific queries
│
├── services/                    # Business logic
│   ├── __init__.py
│   └── user_service.py         # Business rules & orchestration
│
├── factories/                   # Factory pattern
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

## 🔍 Layer Breakdown

### 1. Domain Layer

#### DAO: `domain/models.py` - SQLAlchemy Models

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    """
    DAO (Data Access Object) - database table representation
    ✅ Uses mapped_column and Mapped[type] (SQLAlchemy 2.0)
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
    """Base schema with common fields"""
    email: EmailStr
    username: str

class UserCreate(UserBase):
    """DTO for user creation (input)"""
    password: str

class UserUpdate(BaseModel):
    """DTO for updates (all fields optional)"""
    email: EmailStr | None = None
    username: str | None = None
    password: str | None = None

class UserResponse(UserBase):
    """DTO for API response (output)"""
    id: int
    is_active: bool
    created_at: datetime

    # ✅ Pydantic v2 syntax
    model_config = ConfigDict(from_attributes=True)
```

**Important: Schema vs Model**
- **Schema (Pydantic)**: for API (validation, serialization)
- **Model (SQLAlchemy)**: for DB (persistence, queries)

---

### 2. Repository Layer

#### `repositories/user_repository.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from domain.models import User

class UserRepository:
    """
    Encapsulates ALL database operations
    ✅ All methods are async
    ✅ Uses db.execute() instead of db.query()
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(self, user: User) -> User:
        """Add user"""
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get(self, user_id: int) -> User | None:
        """Get by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Search by email"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        """List with pagination"""
        result = await self.db.execute(
            select(User).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def update(self, user: User) -> User:
        """Update"""
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        """Delete"""
        await self.db.delete(user)
        await self.db.commit()
```

**Benefits:**
- ✅ All SQL in one place
- ✅ Easy to change database
- ✅ Easy to test
- ✅ Query reusability

---

### 3. Factory Pattern

#### `factories/user_factory.py`

```python
from domain.models import User
from domain.schemas import UserCreate

def hash_password(password: str) -> str:
    """Hash password"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

class UserFactory:
    """
    Centralized User entity creation
    """

    @staticmethod
    def create_from_schema(user_create: UserCreate) -> User:
        """
        Convert DTO → DAO
        Schema (Pydantic) → Model (SQLAlchemy)
        """
        return User(
            email=user_create.email,
            username=user_create.username,
            hashed_password=hash_password(user_create.password)
        )
```

**Why use a factory:**
- Centralizes creation logic
- Hides complexity (e.g., hashing)
- Easy to test
- Easy to change creation rules

---

### 4. Unit of Work

#### `unit_of_work.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.user_repository import UserRepository

class UnitOfWork:
    """
    Coordinates repositories and manages transactions
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.users = UserRepository(db)
        # Add other repositories:
        # self.products = ProductRepository(db)
        # self.orders = OrderRepository(db)

    async def commit(self):
        """Commit all changes"""
        await self.db.commit()

    async def rollback(self):
        """Rollback all changes"""
        await self.db.rollback()
```

**Usage:**
```python
async def create_user_with_profile(user_data, profile_data, db):
    uow = UnitOfWork(db)
    try:
        # Create user
        user = await uow.users.add(user_data)
        # Create profile
        profile = await uow.profiles.add(profile_data)
        # Commit both operations together
        await uow.commit()
    except:
        # Rollback both operations on error
        await uow.rollback()
        raise
```

---

### 5. Service Layer

#### `services/user_service.py`

```python
from fastapi import HTTPException
from repositories.user_repository import UserRepository
from factories.user_factory import UserFactory
from domain.schemas import UserCreate, UserUpdate

class UserService:
    """
    Contains business rules
    ✅ All methods async
    """

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def create_user(self, user_create: UserCreate) -> User:
        """
        Create with business rule validation
        """
        # Business rule: email must be unique
        existing = await self.repository.get_by_email(user_create.email)
        if existing:
            raise HTTPException(400, "Email already in use")

        # Use factory for creation
        user = UserFactory.create_from_schema(user_create)

        # Save via repository
        return await self.repository.add(user)

    async def get_user(self, user_id: int) -> User:
        """Get with existence check"""
        user = await self.repository.get(user_id)
        if not user:
            raise HTTPException(404, "User not found")
        return user

    async def update_user(self, user_id: int, user_update: UserUpdate) -> User:
        """Update with validation"""
        user = await self.get_user(user_id)

        # Update only provided fields
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == 'password':
                setattr(user, 'hashed_password', hash_password(value))
            else:
                setattr(user, field, value)

        return await self.repository.update(user)
```

---

### 6. Router Layer

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
    Route does ONLY HTTP logic
    All business logic in service
    """
    return await service.create_user(user)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    """Get user"""
    return await service.get_user(user_id)

@router.get("/", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    repository: UserRepository = Depends(get_repository)
):
    """List users"""
    return await repository.get_all(skip, limit)
```

---

## 🔄 Data Flow

### User Creation:

```
1. POST /users {"email": "john@example.com", "username": "john", "password": "secret"}
   ↓
2. Router validates with UserCreate (Pydantic DTO)
   ↓
3. Service checks business rules (email uniqueness)
   ↓
4. Factory creates User entity (SQLAlchemy DAO)
   ↓
5. Repository saves to DB via await db.execute()
   ↓
6. UnitOfWork commits transaction
   ↓
7. Service returns User (DAO)
   ↓
8. Router converts to UserResponse (DTO)
   ↓
9. HTTP Response: 201 Created with user data
```

---

## 🚀 How to Run

```bash
cd examples/example_06
pip install fastapi uvicorn sqlalchemy aiosqlite pydantic[email]

python main.py
# or
uvicorn main:app --reload
```

Documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 📝 Example Requests

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

## 🎯 DDD Benefits

1. **Separation of Concerns**
   - Each layer does its job
   - Easy to find and change code

2. **Testability**
   - Each layer tested separately
   - Easy to mock dependencies

3. **Maintainability**
   - Changes are localized
   - Clear structure

4. **Scalability**
   - Easy to add new entities
   - Patterns are reusable

5. **Flexibility**
   - Easy to change DB (only repository)
   - Easy to change API (only router)

---

## 📚 Key Patterns

- **Repository**: Data access abstraction
- **Unit of Work**: Transaction management
- **Service Layer**: Business logic
- **Factory**: Object creation
- **DTO**: Data transfer between layers
- **DAO**: Database table representation

---

## 🐛 Common Mistakes

### 1. Confusing Schema and Model

```python
# ❌ WRONG
@router.post("/users")
async def create(user: User):  # User is DAO!
    pass

# ✅ CORRECT
@router.post("/users")
async def create(user: UserCreate):  # UserCreate is DTO!
    pass
```

### 2. Using old SQLAlchemy API

```python
# ❌ WRONG
id = Column(Integer, primary_key=True)
user = db.query(User).first()

# ✅ CORRECT
id: Mapped[int] = mapped_column(Integer, primary_key=True)
result = await db.execute(select(User))
user = result.scalar_one_or_none()
```

### 3. Forgetting async/await

```python
# ❌ WRONG
def get_user(user_id: int):
    return repository.get(user_id)  # No await!

# ✅ CORRECT
async def get_user(user_id: int):
    return await repository.get(user_id)
```

---

## 📝 Practice Tasks

1. ✏️ Add `Product` entity with all layers
2. ✏️ Implement `Order` with many-to-many relationships
3. ✏️ Add authentication (JWT tokens)
4. ✏️ Implement soft delete (is_deleted flag)
5. ✏️ Add event sourcing for audit

---

## 🔗 Useful Links

- [Domain-Driven Design (Eric Evans)](https://www.domainlanguage.com/ddd/)
- [Clean Architecture (Robert Martin)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/advanced/)

---

**This is production-ready architecture for serious applications! 🚀**
