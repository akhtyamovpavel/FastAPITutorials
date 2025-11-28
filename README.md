# FastAPI Tutorial - Comprehensive Guide for Beginners

**[🇷🇺 Русская версия](README_RU.md)**

This tutorial provides a complete learning path from basic FastAPI concepts to advanced Domain-Driven Design architecture.

## 📚 Tutorial Structure

### Example 01: Basic FastAPI Requests

- ✅ GET, POST, PUT, DELETE methods
- ✅ Path parameters (`/items/{item_id}`)
- ✅ Query parameters (`?category=food&limit=10`)
- ✅ Request body validation
- ✅ Response models and status codes
- ✅ **All examples in ONE file**

**File**: `example_01/main.py`

**Topics covered**:
- HTTP methods and when to use them
- URL path parameters vs query parameters
- Request body handling with Pydantic
- Proper HTTP status codes (200, 201, 204, 404)
- Async endpoints with `async def`

---

### Example 02: Pydantic + BaseModel

- ✅ BaseModel basics and field types
- ✅ Advanced validation (Field, field_validator, model_validator)
- ✅ Nested models and complex structures
- ✅ Model configuration (ConfigDict)
- ✅ Custom validators and business logic
- ✅ **All examples in ONE file**

**File**: `example_02/main.py`

**Topics covered**:
- Pydantic v2 syntax and best practices
- Field constraints (min_length, max_length, pattern, gt, le)
- EmailStr, HttpUrl, and other special types
- Nested models for complex data structures
- Request/Response model separation
- Error handling and validation errors

---

### Example 03: Database Integration (SQLAlchemy Async)

- ✅ Async SQLAlchemy 2.0 configuration
- ✅ Session management with `Depends(get_db)`
- ✅ Modern ORM: `mapped_column` and `Mapped[type]` (NOT old `Column`)
- ✅ Using `db.execute(select(...))` instead of `db.query(...)`
- ✅ **Schema vs Model explained** - Key difference!
- ✅ Complete CRUD operations
- ✅ **All examples in ONE file**

**File**: `example_03/main.py`

**Key Concepts**:

**Schema (Pydantic)** - API Layer:
- Validates incoming data from clients
- Serializes outgoing data to clients
- Lives in the application/API layer
- Examples: `UserCreate`, `UserUpdate`, `UserResponse`

**Model (SQLAlchemy)** - Database Layer:
- Represents database table structure
- Maps Python objects to database rows
- Lives in the data/persistence layer
- Example: `User` class with `mapped_column`

**Why both?**:
- Separation of concerns
- Database schema can differ from API contract
- Can hide sensitive fields (passwords, internal IDs)
- Multiple Pydantic schemas can use same Model

---

### Example 04: Image Handling

- ✅ File upload with validation
- ✅ Image processing (resize, convert format)
- ✅ PIL/Pillow library usage
- ✅ File download (FileResponse, StreamingResponse)
- ✅ Static file serving
- ✅ On-the-fly thumbnail generation
- ✅ File system operations

**File**: `example_04/main.py`

**Key Operations**:
- Upload image with type validation
- Resize images maintaining aspect ratio
- Convert between formats (JPEG, PNG, WEBP)
- Download processed images
- Stream thumbnails without saving
- List uploaded and processed files

**Technologies**:
- FastAPI file upload (`UploadFile`)
- PIL/Pillow for image processing
- `FileResponse` for downloads
- `StreamingResponse` for streaming
- `StaticFiles` for serving directories

---

### Example 05: Dependency Injection

- ✅ How `Depends()` works internally
- ✅ Service layer pattern with DI
- ✅ Repository pattern for data access
- ✅ Multi-level dependency chain
- ✅ Testing benefits of DI
- ✅ Request-scoped dependency caching

**Files**: `example_05/main.py`, `example_05/test_di.py`

**Dependency Chain**:
```
Router → Service → Repository → Database Session
```

**How Depends() Works**:
1. FastAPI analyzes function signature
2. Recursively resolves all dependencies
3. Caches instances per request (same session for all)
4. Calls cleanup code (generators with `yield`)
5. Injects resolved dependencies into function

**Benefits**:
- Easy to test (can override dependencies)
- Clean separation of concerns
- Automatic resource management
- Type-safe dependency injection
- Reusable components

---

### Example 06: Domain-Driven Design (Full Architecture)

Complete professional architecture with clear separation of layers.

**Files**:
```
example_06/
├── domain/
│   ├── models.py      # DAO: Database models (SQLAlchemy)
│   └── schemas.py     # DTO: Data Transfer Objects (Pydantic)
├── repositories/
│   ├── base.py        # Generic CRUD repository
│   └── user_repository.py  # User-specific queries
├── services/
│   └── user_service.py     # Business logic layer
├── factories/
│   └── user_factory.py     # Object creation patterns
├── routers/
│   └── users.py       # HTTP API endpoints (thin layer)
├── database.py        # Database configuration
├── unit_of_work.py    # Transaction management
└── main.py            # Application entry point
```

**Architecture Layers**:

1. **DAO (Data Access Objects)** - `domain/models.py`
   - SQLAlchemy ORM models
   - Database table representation

2. **DTO (Data Transfer Objects)** - `domain/schemas.py`
   - Pydantic models for API contracts
   - Validation and serialization

3. **Repositories** - Data access abstraction
4. **Services** - Business logic layer
5. **Factories** - Object creation patterns
6. **UnitOfWork** - Transaction management
7. **Routers** - Thin HTTP layer

---

## 🚀 Getting Started

### Installation

```bash
# Install all dependencies
pip install -r requirements.txt

# Or install for specific example
cd example_01
pip install fastapi uvicorn pydantic[email]
```

### Running Examples

**Example 01-03** (single file):
```bash
cd example_01  # or example_02, example_03
uvicorn main:app --reload
```

**Example 04-06** (multiple files or single file):
```bash
cd example_04  # or example_05, example_06
python main.py
```

**Access API docs**:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 📖 Learning Path

### Beginner
1. Start with **Example 01** - Learn basic HTTP methods
2. Move to **Example 02** - Master Pydantic validation
3. Study **Example 03** - Understand database integration

### Intermediate
4. **Example 04** - Learn file handling and image processing
5. **Example 05** - Learn Dependency Injection pattern
6. Understand Service and Repository layers

### Advanced
7. **Example 06** - Full DDD architecture
8. Build production-ready applications

---

## 🔑 Key Differences Explained

### Schema vs Model (Example 03)

**Schema (Pydantic)**:
- For API validation and serialization
- Lives in application layer
- Examples: `UserCreate`, `UserResponse`

**Model (SQLAlchemy)**:
- For database representation
- Lives in persistence layer
- Example: `User` with `mapped_column`

### Old vs New SQLAlchemy

**❌ OLD (SQLAlchemy 1.x)**:
```python
id = Column(Integer, primary_key=True)
user = db.query(User).filter(User.id == 1).first()
```

**✅ NEW (SQLAlchemy 2.0)** - Used in this tutorial:
```python
id: Mapped[int] = mapped_column(Integer, primary_key=True)
result = await db.execute(select(User).where(User.id == 1))
user = result.scalar_one_or_none()
```

**Benefits**:
- Better type checking with Mapped[type]
- IDE autocomplete support
- Async/await native support
- Unified query API
- Better performance

---

## 🎯 Critical Requirements

✅ **100% Async Code**
- All endpoints use `async def`
- All database operations use `await`
- AsyncSession for database
- Async context managers

✅ **SQLAlchemy 2.0 Patterns**
- `mapped_column` instead of `Column`
- `Mapped[type]` for type hints
- `db.execute(select(...))` instead of `db.query(...)`

✅ **File Organization**
- Examples 1-4: All code in ONE file (simple structure)
- Examples 5-6: Proper layer separation (advanced architecture)
- No files in root folder (all in subdirectories)

---

## 🧪 Testing

Run tests for Example 05:
```bash
cd example_05
pytest test_di.py -v
```

Tests demonstrate:
- Integration testing with test database
- Dependency override patterns
- Mocking repositories
- Benefits of DI for testing

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- [Pydantic v2](https://docs.pydantic.dev/latest/)
- [Domain-Driven Design](https://martinfowler.com/tags/domain%20driven%20design.html)

---

## 🤝 Contributing

This is a teaching project. Each example is self-contained and can be studied independently.

Suggestions for improvement are welcome!

---

## 📄 License

Educational material under MIT License.
---

**Happy Learning! 🚀**
