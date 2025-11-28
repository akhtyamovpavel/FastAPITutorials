# Example 03: Async SQLAlchemy 2.0 + Database Integration

**[🇷🇺 Русская версия](README_RU.md)**

---

## 📚 What You'll Learn

In this example, we cover modern database work:
- ✅ **Async SQLAlchemy 2.0** (all operations are asynchronous!)
- ✅ **`db.execute(select(...))` instead of `db.query()`** - new API
- ✅ **`mapped_column` and `Mapped[type]` instead of `Column`** - modern ORM
- ✅ **Schema (Pydantic) vs Model (SQLAlchemy)** - key difference!
- ✅ CRUD operations (Create, Read, Update, Delete)
- ✅ Dependency Injection via `Depends(get_db)`
- ✅ Async session management
- ✅ **All examples in ONE file** (main.py)

## 🎯 CRITICALLY IMPORTANT: Schema vs Model

### ❌ Common Beginner Mistake:
```python
@app.post("/users")
async def create_user(user: UserModel):  # WRONG!
    # UserModel is a SQLAlchemy ORM model for the database
    # Cannot be used for API!
    pass
```

### ✅ Correct Approach:

```python
# Schema (Pydantic) - for API
class UserCreate(BaseModel):
    """What we accept from the client via API"""
    email: EmailStr
    username: str
    password: str

# Model (SQLAlchemy) - for Database
class User(Base):
    """How it's stored in the database"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str] = mapped_column(String)

@app.post("/users")
async def create_user(
    user: UserCreate,              # Schema for validation
    db: AsyncSession = Depends(get_db)
):
    # Convert Schema → Model
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

## 📊 Differences Table

| Aspect | Schema (Pydantic) | Model (SQLAlchemy) |
|--------|-------------------|-------------------|
| **Purpose** | API validation and serialization | Database table |
| **Where it lives** | Application layer | Database layer |
| **Inherits from** | `BaseModel` | `Base` |
| **Field types** | Python types (`str`, `int`) | SQL types (`String`, `Integer`) |
| **Validation** | Input/output API data | Table structure |
| **Examples** | `UserCreate`, `UserResponse` | `User`, `Product` |

### Why do we need both?

1. **Security**: hide internal fields (passwords, tokens)
2. **Flexibility**: API can differ from database
3. **Multiplicity**: one database model → many API schemas
4. **Separation of concerns**: API doesn't know about database

### Workflow Example:

```
Client → JSON → UserCreate (Schema) → validation
                                ↓
                        User (Model) → Database
                                ↓
                  UserResponse (Schema) ← serialization
                                ↓
                        JSON → Client
```

---

## 🚀 How to Run

```bash
# Install dependencies
pip install fastapi uvicorn sqlalchemy aiosqlite pydantic[email]

# Start server
cd example_03
uvicorn main:app --reload
```

Database will be created automatically: `example_03.db`

Documentation: `http://localhost:8000/docs`

---

## ⚡ SQLAlchemy 2.0: Old vs New API

### ❌ OLD WAY (SQLAlchemy 1.x - NOT used!)

```python
# Synchronous Session
from sqlalchemy.orm import Session

class User(Base):
    __tablename__ = "users"

    # Old Column without types
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

def get_user(db: Session, user_id: int):
    # Old query API
    user = db.query(User).filter(User.id == user_id).first()
    return user

@app.get("/users/{user_id}")
def get(user_id: int, db: Session = Depends(get_db)):
    # Synchronous code - blocks the server!
    return get_user(db, user_id)
```

### ✅ NEW WAY (SQLAlchemy 2.0 - used in example!)

```python
# Async AsyncSession
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import select

class User(Base):
    __tablename__ = "users"

    # New mapped_column with Mapped types
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

async def get_user(db: AsyncSession, user_id: int):
    # New execute + select API
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    return user

@app.get("/users/{user_id}")
async def get(user_id: int, db: AsyncSession = Depends(get_db)):
    # Async code - doesn't block!
    return await get_user(db, user_id)
```

---

## 🔄 Migration Patterns

### 1. Model Definition

```python
# ❌ OLD (Column)
class User(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True)

# ✅ NEW (mapped_column + Mapped)
class User(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True)
```

### 2. Query Execution

```python
# ❌ OLD (query)
users = db.query(User).filter(User.age > 18).all()

# ✅ NEW (execute + select)
result = await db.execute(
    select(User).where(User.age > 18)
)
users = result.scalars().all()
```

### 3. Get Single Record

```python
# ❌ OLD (.first())
user = db.query(User).filter(User.id == 1).first()

# ✅ NEW (scalar_one_or_none)
result = await db.execute(
    select(User).where(User.id == 1)
)
user = result.scalar_one_or_none()
```

### 4. Count Records

```python
# ❌ OLD (.count())
count = db.query(User).count()

# ✅ NEW (func.count)
from sqlalchemy import func
result = await db.execute(
    select(func.count()).select_from(User)
)
count = result.scalar()
```

---

## 🔍 Component Breakdown

### 1. Async Database Setup

```python
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)

engine = create_async_engine(
    "sqlite+aiosqlite:///./example_03.db",
    echo=True  # SQL query logging
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

**Important:**
- `create_async_engine` instead of `create_engine`
- `async_sessionmaker` instead of `sessionmaker`
- `AsyncSession` instead of `Session`
- `yield` to pass the session
- `await session.close()` for proper cleanup

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

    # ✅ Mapped types for better IDE support
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

**Mapped advantages:**
- IDE autocomplete works perfectly
- Catches type errors during development
- Cleaner and more understandable code
- Follows SQLAlchemy 2.0 best practices

---

### 3. Pydantic Schemas (DTOs)

```python
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

# Base schema
class UserBase(BaseModel):
    email: EmailStr
    username: str

# For creation (input)
class UserCreate(UserBase):
    password: str  # Accept plain password

# For update (input)
class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = None
    password: str | None = None

# For API response (output)
class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    # ✅ Pydantic v2 - from_attributes instead of orm_mode
    model_config = ConfigDict(from_attributes=True)
```

**Important (Pydantic v2):**
- `from_attributes=True` replaces old `orm_mode=True`
- `model_config = ConfigDict()` replaces `class Config`
- Allows creating schemas from ORM models:
  ```python
  user_response = UserResponse.from_orm(db_user)
  ```

---

### 4. CRUD Operations - Modern Style

#### CREATE

```python
@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    # Check email uniqueness
    result = await db.execute(
        select(User).where(User.email == user.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(400, "Email already in use")

    # Schema → Model
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hash_password(user.password)  # Hash it!
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
    # ✅ New style: select + execute + scalars
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
        raise HTTPException(404, "User not found")

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
    # Find in database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(404, "Not found")

    # Update only provided fields
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
        raise HTTPException(404, "Not found")

    await db.delete(db_user)
    await db.commit()

    return None  # 204 No Content
```

---

## 📋 Result Object Methods

```python
result = await db.execute(select(User))

# Get single scalar (single value)
user = result.scalar_one()          # ❌ Error if none or > 1
user = result.scalar_one_or_none()  # ✅ None if none
user = result.scalar()              # ✅ None if none, first if > 1

# Get multiple scalars
users = result.scalars().all()      # ✅ List of User objects

# Get Row (tuple)
row = result.one()                  # ❌ Error if none or > 1
rows = result.all()                 # ✅ List of tuples
```

---

## 🎯 Best Practices

### 1. Always use async/await

```python
# ✅ CORRECT
@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()

# ❌ WRONG
@app.get("/users")
def get_users(db: AsyncSession = Depends(get_db)):
    # No async - won't work!
    result = db.execute(select(User))
    return result.scalars().all()
```

### 2. Use mapped_column and Mapped

```python
# ✅ CORRECT (SQLAlchemy 2.0)
class User(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)

# ❌ WRONG (deprecated syntax)
class User(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String)
```

### 3. Separate Schema and Model

```python
# ✅ CORRECT
UserCreate, UserUpdate, UserResponse - for API (Pydantic)
User - for database (SQLAlchemy)

# ❌ WRONG
One model for everything
```

### 4. Use Depends(get_db)

```python
# ✅ CORRECT
async def my_route(db: AsyncSession = Depends(get_db)):
    # Session will close automatically
    pass

# ❌ WRONG
async def my_route():
    async with AsyncSessionLocal() as db:
        # Code duplication
        pass
```

---

## 📝 Practice Tasks

1. ✏️ Add `posts` table with many-to-one relationship to `users`
2. ✏️ Implement soft delete (`deleted_at` field)
3. ✏️ Add full-text search for users
4. ✏️ Create endpoint for bulk user insert
5. ✏️ Add pagination with metadata (total_count, pages)

---

## 🐛 Common Mistakes

### 1. Using old .query() API

```python
# ❌ WRONG (SQLAlchemy 1.x)
users = db.query(User).all()

# ✅ CORRECT (SQLAlchemy 2.0)
result = await db.execute(select(User))
users = result.scalars().all()
```

### 2. Forgot await

```python
# ❌ WRONG
result = db.execute(select(User))  # No await!

# ✅ CORRECT
result = await db.execute(select(User))
```

### 3. Using Column instead of mapped_column

```python
# ❌ WRONG
id = Column(Integer, primary_key=True)

# ✅ CORRECT
id: Mapped[int] = mapped_column(Integer, primary_key=True)
```

### 4. Confusing Schema and Model

```python
# ❌ WRONG
@app.post("/users")
async def create(user: User):  # User is a SQLAlchemy model!
    pass

# ✅ CORRECT
@app.post("/users")
async def create(user: UserCreate):  # UserCreate is a Pydantic schema
    pass
```

---

## 🔗 Next Steps

Move on to **Example 04**, where we'll study **Dependency Injection** and the **Service Layer** pattern in detail!

**What you'll learn:**
- How `Depends()` works internally
- Repository pattern
- Service layer for business logic
- Dependency chains
