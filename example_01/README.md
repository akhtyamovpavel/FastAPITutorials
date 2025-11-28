# Example 01: Basic FastAPI Requests

**[🇷🇺 Русская версия](README_RU.md)**

## 📚 What You'll Learn

In this example, we cover the basics of working with HTTP requests in FastAPI:
- ✅ **Asynchronous** GET, POST, PUT, DELETE requests (async/await)
- ✅ Path parameters
- ✅ Query parameters
- ✅ Body parameters
- ✅ Data validation with Pydantic
- ✅ **All examples in ONE file** (main.py)

## 🚀 How to Run

```bash
# Install dependencies
pip install fastapi uvicorn pydantic[email]

# Run server
cd example_01
uvicorn main:app --reload

# Or via Python
python -m uvicorn main:app --reload
```

Server will start at `http://localhost:8000`

## 📖 API Documentation

FastAPI automatically generates interactive documentation:
- **Swagger UI**: `http://localhost:8000/docs` ⭐ (recommended)
- **ReDoc**: `http://localhost:8000/redoc`

## ⚡ Why async/await?

```python
# ✅ Asynchronous code (used in this example)
@app.get("/items")
async def get_items():
    # Can handle thousands of requests simultaneously
    return items

# ❌ Synchronous code (NOT used)
@app.get("/items")
def get_items():
    # Blocks the server during execution
    return items
```

**Async advantages:**
- High performance (10x-100x faster for I/O operations)
- Doesn't block other requests
- Ready for async databases (Example 03)

## 🔍 Endpoint Examples

### 1. Simple GET Request

```python
@app.get("/")
async def read_root():
    return {"message": "Hello, FastAPI!"}
```

**Testing:**
```bash
curl http://localhost:8000/
# Response: {"message": "Hello, FastAPI!"}
```

---

### 2. GET with Path Parameter

```python
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id, "name": f"Item {item_id}"}
```

**Testing:**
```bash
curl http://localhost:8000/items/42
# ✅ Response: {"item_id": 42, "name": "Item 42"}

curl http://localhost:8000/items/abc
# ❌ Error 422: item_id must be int
```

**Important:**
- `{item_id}` - path parameter
- `item_id: int` - automatic validation and conversion
- Wrong type → 422 Unprocessable Entity error

---

### 3. GET with Query Parameters

```python
@app.get("/items")
async def list_items(
    category: str = Query(None),        # Optional
    skip: int = Query(0, ge=0),         # Default 0, >= 0
    limit: int = Query(10, ge=1, le=100) # From 1 to 100
):
    # Filtering and pagination
    ...
```

**Testing:**
```bash
# Basic request (default values)
curl http://localhost:8000/items

# With parameters
curl "http://localhost:8000/items?category=electronics&skip=0&limit=20"

# Validation works
curl "http://localhost:8000/items?limit=200"
# ❌ Error: limit must be <= 100
```

**Query validators:**
- `ge` (greater or equal)
- `le` (less or equal)
- `gt` (greater than)
- `lt` (less than)
- `min_length`, `max_length` - for strings

---

### 4. POST Request with Pydantic Model

```python
from pydantic import BaseModel, Field

class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    description: str | None = None

@app.post("/items", status_code=201)
async def create_item(item: ItemCreate):
    # item is already validated!
    return {"id": 1, **item.dict()}
```

**Testing:**
```bash
# ✅ Correct request
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Laptop",
    "price": 50000,
    "description": "Gaming laptop"
  }'

# ❌ Negative price
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Item", "price": -100}'
# Error: price must be > 0
```

**Pydantic advantages:**
- Automatic type validation
- Detailed error messages
- Automatic API documentation
- Type hints for IDE

---

### 5. PUT Request for Updates

```python
class ItemUpdate(BaseModel):
    name: str | None = None
    price: float | None = Field(None, gt=0)
    # All fields optional for partial updates

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: ItemUpdate):
    # Update only provided fields
    update_data = item.dict(exclude_unset=True)
    return {"item_id": item_id, **update_data}
```

**Testing:**
```bash
# Update only name
curl -X PUT http://localhost:8000/items/5 \
  -H "Content-Type: application/json" \
  -d '{"name": "New name"}'

# Update multiple fields
curl -X PUT http://localhost:8000/items/5 \
  -H "Content-Type: application/json" \
  -d '{"name": "Item", "price": 20000}'
```

---

### 6. DELETE Request

```python
@app.delete("/items/{item_id}", status_code=204)
async def delete_item(item_id: int = Path(..., gt=0)):
    # Delete item
    return None  # 204 No Content - no response body
```

**Testing:**
```bash
curl -X DELETE http://localhost:8000/items/42
# Response: empty (204 No Content)
```

**HTTP status codes:**
- `200 OK` - successful GET
- `201 Created` - successful POST
- `204 No Content` - successful DELETE
- `404 Not Found` - resource not found
- `422 Unprocessable Entity` - validation error

---

## 🎯 Key Concepts

### Path vs Query vs Body Parameters

| Type | Where | Example | Usage |
|------|-------|---------|-------|
| **Path** | In URL path | `/items/{id}` | Resource identification |
| **Query** | After `?` | `?skip=0&limit=10` | Filters, pagination |
| **Body** | In request body | `{"name": "..."}` | Create/update |

### Async/Await - Mandatory!

```python
# ✅ Correct (all examples use async)
@app.get("/items")
async def get_items():
    return items

# ❌ Not used in this tutorial
@app.get("/items")
def get_items():
    return items
```

### Pydantic Validation

```python
# Automatic validation
class Item(BaseModel):
    name: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)

    # Custom validation
    @field_validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v
```

## 📝 Practice Tasks

1. ✏️ Add endpoint `GET /items/{item_id}/reviews` with query parameter `rating_min`
2. ✏️ Create `PATCH /items/{item_id}` for partial updates
3. ✏️ Add price range filtering: `min_price` and `max_price`
4. ✏️ Implement `POST /items/bulk` to create multiple items
5. ✏️ Add search with `GET /items/search?q=keyword`

## 🐛 Common Mistakes

### 1. Forgot async
```python
# ❌ WRONG
@app.get("/items")
def get_items():  # No async!
    return items

# ✅ CORRECT
@app.get("/items")
async def get_items():
    return items
```

### 2. Wrong parameter order
```python
# ❌ WRONG
async def func(name: str = Body(None), item_id: int):
    pass

# ✅ CORRECT
async def func(item_id: int, name: str = Body(None)):
    pass
```

### 3. Forgot Content-Type
```bash
# ❌ WRONG
curl -X POST http://localhost:8000/items -d '{"name": "test"}'

# ✅ CORRECT
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name": "test"}'
```

## 📚 Next Steps

After studying this example, proceed to:
- **Example 02**: Advanced Pydantic validation
- **Example 03**: Database integration (async SQLAlchemy 2.0)
- **Example 04**: Dependency Injection patterns
- **Example 05**: Full DDD architecture

## 🔗 Useful Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [HTTP Status Codes](https://httpstatuses.com/)

---

**Tip**: Use Swagger UI (`/docs`) for interactive testing of all endpoints!
