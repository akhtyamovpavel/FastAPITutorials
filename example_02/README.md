# Example 02: Pydantic + BaseModel

**[🇷🇺 Русская версия](README_RU.md)**

## 📚 What You'll Learn

In this example, we explore advanced validation with Pydantic v2:
- ✅ BaseModel and structured data
- ✅ Field validation via `Field()` and `@field_validator`
- ✅ Nested models
- ✅ Enum for value constraints
- ✅ ConfigDict for model configuration (Pydantic v2)
- ✅ Model separation: Create, Update, Response, InDB
- ✅ **All examples in ONE file** (main.py)
- ✅ **All endpoints are async** (async/await)

## 🚀 How to Run

```bash
# Install dependencies
pip install fastapi uvicorn pydantic[email]

# Start server
cd example_02
uvicorn main:app --reload
```

API Documentation: `http://localhost:8000/docs`

## 🎯 Why Pydantic?

### Without Pydantic (Example 01):
```python
@app.post("/items")
async def create_item(
    name: str = Body(...),
    price: float = Body(...),
    description: str = Body(None),
    category: str = Body(...),
    tags: list = Body([])
):
    # 😰 Too many parameters!
    # 😰 Validation scattered across code
    # 😰 Hard to read and maintain
    pass
```

### With Pydantic:
```python
class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    description: str | None = None
    category: str
    tags: list[str] = []

@app.post("/items")
async def create_item(item: ItemCreate):
    # ✅ Clean and clear
    # ✅ Validation in model
    # ✅ IDE autocomplete
    pass
```

## 🔍 Examples

### 1. Basic Model

```python
from pydantic import BaseModel

class User(BaseModel):
    username: str
    email: str
    age: int | None = None  # Optional (Python 3.10+)
```

**Usage:**
```python
# Create
user = User(username="john", email="john@example.com", age=25)

# Validation
user = User(username="john", email="john@example.com", age="invalid")
# ❌ ValidationError: age must be int
```

---

### 2. Field() - Advanced Validation

```python
from pydantic import Field, EmailStr

class Product(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0, le=1000000)
    sku: str = Field(..., pattern=r'^[A-Z]{3}-\d{6}$')
    email: EmailStr  # Automatic email validation
```

**Field Validators:**
- `min_length`, `max_length` - for strings
- `gt`, `ge`, `lt`, `le` - for numbers
- `pattern` - regex for strings
- `max_items` - for lists

**Testing:**
```bash
curl -X POST http://localhost:8000/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Laptop",
    "price": 50000,
    "sku": "LAP-123456",
    "quantity": 10
  }'
```

---

### 3. Enum for Limited Values

```python
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class Order(BaseModel):
    order_id: int
    status: OrderStatus  # Only values from Enum!
```

**Benefits:**
- IDE autocompletes possible values
- Protection from typos
- Automatic Swagger documentation

**Testing:**
```bash
# ✅ Correct
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"order_id": 1, "status": "pending", "items": ["item1"], "total": 1000}'

# ❌ Incorrect
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"order_id": 1, "status": "invalid", "items": ["item1"], "total": 1000}'
# Error: status must be one of: pending, processing, shipped, delivered, cancelled
```

---

### 4. Custom Validators (Pydantic v2)

```python
from pydantic import field_validator, model_validator

class User(BaseModel):
    username: str
    password: str
    age: int | None = None

    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        """Field-level validation"""
        if not v.replace('_', '').isalnum():
            raise ValueError('Only letters, numbers and _')
        return v

    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Password strength check"""
        if len(v) < 8:
            raise ValueError('Minimum 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('Need at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Need uppercase letter')
        return v

    @model_validator(mode='after')
    def check_age_restriction(self) -> 'User':
        """Model-level validation"""
        if self.age is not None and self.age < 18:
            raise ValueError('18+ only')
        return self
```

**Important (Pydantic v2):**
- Use `@field_validator` instead of old `@validator`
- Must add `@classmethod`
- `@model_validator` for whole model validation

---

### 5. Nested Models

```python
class Address(BaseModel):
    street: str
    city: str
    postal_code: str
    country: str = "Russia"

class ContactInfo(BaseModel):
    email: EmailStr
    phone: str = Field(..., pattern=r'^\+?\d{10,15}$')

class UserProfile(BaseModel):
    name: str
    contact: ContactInfo      # Nested model!
    address: Address | None = None  # Optional nested
```

**Testing:**
```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123",
    "age": 25,
    "profile": {
      "full_name": "John Doe",
      "phone": "+79991234567",
      "address": {
        "street": "Lenin 1",
        "city": "Moscow",
        "postal_code": "123456"
      }
    }
  }'
```

---

### 6. ConfigDict - Model Configuration (Pydantic v2)

```python
from pydantic import ConfigDict

class User(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,    # Strip whitespace from strings
        validate_assignment=True,      # Validate on assignment
        extra='forbid',                # Forbid extra fields
        from_attributes=True           # For ORM (was orm_mode)
    )

    username: str
    email: EmailStr
```

**Important changes in Pydantic v2:**
- `orm_mode = True` → `from_attributes=True`
- `class Config` → `model_config = ConfigDict()`
- Stricter validation by default

---

### 7. Model Separation: Create, Update, Response, InDB

```python
# Base model with common fields
class ItemBase(BaseModel):
    name: str
    price: float

# For creation - input data from client
class ItemCreate(ItemBase):
    description: str | None = None
    quantity: int = 1

# For update - all fields optional
class ItemUpdate(BaseModel):
    name: str | None = None
    price: float | None = Field(None, gt=0)
    description: str | None = None
    quantity: int | None = Field(None, ge=0)

# For API response - add auto-generated fields
class ItemResponse(ItemBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# For DB storage - may contain service fields
class ItemInDB(ItemResponse):
    hashed_password: str | None = None
    is_deleted: bool = False
```

**Why separate?**

1. **ItemCreate** - what we accept from client
   ```python
   @app.post("/items")
   async def create(item: ItemCreate):
       pass
   ```

2. **ItemUpdate** - for partial updates
   ```python
   @app.patch("/items/{id}")
   async def update(id: int, item: ItemUpdate):
       # Update only provided fields
       update_data = item.model_dump(exclude_unset=True)
       pass
   ```

3. **ItemResponse** - what we return to client (hide service fields)
   ```python
   @app.get("/items/{id}", response_model=ItemResponse)
   async def get(id: int):
       return db_item  # hashed_password won't be in response!
   ```

4. **ItemInDB** - full model for DB operations

---

## 📊 Useful Pydantic v2 Methods

```python
item = Item(name="Product", price=100)

# Convert to dict (Pydantic v2)
item.model_dump()
# {'name': 'Product', 'price': 100, 'description': None}

# Only set fields
item.model_dump(exclude_unset=True)
# {'name': 'Product', 'price': 100}

# Exclude specific fields
item.model_dump(exclude={'description'})

# JSON string
item.model_dump_json()

# Create from dict
item = Item.model_validate({'name': 'Product', 'price': 100})
```

**Important changes in Pydantic v2:**
- `.dict()` → `.model_dump()`
- `.json()` → `.model_dump_json()`
- `.parse_obj()` → `.model_validate()`

## 🎯 Key Concepts

### Async endpoints - required!

```python
# ✅ All examples use async
@app.post("/items")
async def create_item(item: ItemCreate):
    return item

# ❌ NOT used
@app.post("/items")
def create_item(item: ItemCreate):
    return item
```

### Pydantic v2 vs v1

| v1 (old) | v2 (new, we use) |
|----------|------------------|
| `@validator` | `@field_validator` |
| `class Config` | `model_config = ConfigDict()` |
| `orm_mode = True` | `from_attributes=True` |
| `.dict()` | `.model_dump()` |
| `.json()` | `.model_dump_json()` |

## 📝 Practice Tasks

1. ✏️ Create a `Book` model with ISBN format validation
2. ✏️ Implement a comment system with nested models `Comment` and `Author`
3. ✏️ Add custom validator for age verification (18+)
4. ✏️ Create a blog API with `PostCreate`, `PostUpdate`, `PostResponse`
5. ✏️ Use Enum for post status (`draft`, `published`, `archived`)

## 🐛 Common Mistakes

### 1. Using Pydantic v1 syntax

```python
# ❌ WRONG (Pydantic v1)
class User(BaseModel):
    class Config:
        orm_mode = True

    @validator('username')
    def check_username(cls, v):
        return v

# ✅ CORRECT (Pydantic v2)
class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_validator('username')
    @classmethod
    def check_username(cls, v):
        return v
```

### 2. Forgot exclude_unset for PATCH

```python
# ❌ WRONG - all fields become None
update_data = item_update.model_dump()

# ✅ CORRECT - only provided fields
update_data = item_update.model_dump(exclude_unset=True)
```

### 3. Missing dependencies

```bash
pip install email-validator  # for EmailStr
pip install pydantic[email]  # or this way
```

## 🔗 Next Steps

Move on to **Example 03**, where we integrate **async SQLAlchemy 2.0** and learn database operations!

**Important topics in Example 03:**
- Async database operations
- Using `db.execute(select(...))` instead of `db.query()`
- `mapped_column` and `Mapped[type]` instead of `Column`
- **Key concept: Schema (Pydantic) vs Model (SQLAlchemy)**

---

**Tip**: All examples in this file use Pydantic v2 and async/await!
