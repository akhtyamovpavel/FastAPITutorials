# Example 01: Базовые запросы в FastAPI

**[🇬🇧 English version](README.md)**

## 📚 Что изучаем

В этом примере разбираем основы работы с HTTP запросами в FastAPI:
- ✅ **Асинхронные** GET, POST, PUT, DELETE запросы (async/await)
- ✅ Path параметры (параметры пути)
- ✅ Query параметры (параметры запроса)
- ✅ Body параметры (тело запроса)
- ✅ Валидация данных с Pydantic
- ✅ **Все примеры в ОДНОМ файле** (main.py)

## 🚀 Как запустить

```bash
# Установить зависимости
pip install fastapi uvicorn pydantic[email]

# Запустить сервер
cd example_01
uvicorn main:app --reload

# Или через Python
python -m uvicorn main:app --reload
```

Сервер запустится на `http://localhost:8000`

## 📖 Документация API

FastAPI автоматически генерирует интерактивную документацию:
- **Swagger UI**: `http://localhost:8000/docs` ⭐ (рекомендуется)
- **ReDoc**: `http://localhost:8000/redoc`

## ⚡ Почему async/await?

```python
# ✅ Асинхронный код (используется в этом примере)
@app.get("/items")
async def get_items():
    # Может обрабатывать тысячи запросов одновременно
    return items

# ❌ Синхронный код (НЕ используется)
@app.get("/items")
def get_items():
    # Блокирует сервер на время выполнения
    return items
```

**Преимущества async:**
- Высокая производительность (10x-100x быстрее для I/O операций)
- Не блокирует другие запросы
- Готов к работе с async базами данных (Example 03)

## 🔍 Разбор эндпоинтов

### 1. Простой GET запрос

```python
@app.get("/")
async def read_root():
    return {"message": "Привет, FastAPI!"}
```

**Тестирование:**
```bash
curl http://localhost:8000/
# Ответ: {"message": "Привет, FastAPI!"}
```

---

### 2. GET с path параметром

```python
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id, "name": f"Товар {item_id}"}
```

**Тестирование:**
```bash
curl http://localhost:8000/items/42
# ✅ Ответ: {"item_id": 42, "name": "Товар 42"}

curl http://localhost:8000/items/abc
# ❌ Ошибка 422: item_id должен быть int
```

**Важно:**
- `{item_id}` - path параметр
- `item_id: int` - автоматическая валидация и конвертация
- Неверный тип → ошибка 422 Unprocessable Entity

---

### 3. GET с query параметрами

```python
@app.get("/items")
async def list_items(
    category: str = Query(None),        # Опциональный
    skip: int = Query(0, ge=0),         # По умолчанию 0, >= 0
    limit: int = Query(10, ge=1, le=100) # От 1 до 100
):
    # Фильтрация и пагинация
    ...
```

**Тестирование:**
```bash
# Базовый запрос (дефолтные значения)
curl http://localhost:8000/items

# С параметрами
curl "http://localhost:8000/items?category=electronics&skip=0&limit=20"

# Валидация работает
curl "http://localhost:8000/items?limit=200"
# ❌ Ошибка: limit должен быть <= 100
```

**Валидаторы Query:**
- `ge` (greater or equal) - больше или равно
- `le` (less or equal) - меньше или равно
- `gt` (greater than) - строго больше
- `lt` (less than) - строго меньше
- `min_length`, `max_length` - для строк

---

### 4. POST запрос с Pydantic моделью

```python
from pydantic import BaseModel, Field

class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    description: str | None = None

@app.post("/items", status_code=201)
async def create_item(item: ItemCreate):
    # item уже провалидирован!
    return {"id": 1, **item.dict()}
```

**Тестирование:**
```bash
# ✅ Правильный запрос
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ноутбук",
    "price": 50000,
    "description": "Игровой ноутбук"
  }'

# ❌ Отрицательная цена
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Товар", "price": -100}'
# Ошибка: price должен быть > 0
```

**Преимущества Pydantic:**
- Автоматическая валидация типов
- Детальные сообщения об ошибках
- Автоматическая документация API
- Type hints для IDE

---

### 5. PUT запрос для обновления

```python
class ItemUpdate(BaseModel):
    name: str | None = None
    price: float | None = Field(None, gt=0)
    # Все поля опциональные для частичного обновления

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: ItemUpdate):
    # Обновляем только переданные поля
    update_data = item.dict(exclude_unset=True)
    return {"item_id": item_id, **update_data}
```

**Тестирование:**
```bash
# Обновить только имя
curl -X PUT http://localhost:8000/items/5 \
  -H "Content-Type: application/json" \
  -d '{"name": "Новое название"}'

# Обновить несколько полей
curl -X PUT http://localhost:8000/items/5 \
  -H "Content-Type: application/json" \
  -d '{"name": "Товар", "price": 20000}'
```

---

### 6. DELETE запрос

```python
@app.delete("/items/{item_id}", status_code=204)
async def delete_item(item_id: int = Path(..., gt=0)):
    # Удаление товара
    return None  # 204 No Content - нет тела ответа
```

**Тестирование:**
```bash
curl -X DELETE http://localhost:8000/items/42
# Ответ: пустой (204 No Content)
```

**HTTP коды статуса:**
- `200 OK` - успешный GET
- `201 Created` - успешный POST
- `204 No Content` - успешный DELETE
- `404 Not Found` - ресурс не найден
- `422 Unprocessable Entity` - ошибка валидации

---

## 🎯 Ключевые концепции

### Path vs Query vs Body параметры

| Тип | Где | Пример | Использование |
|-----|-----|--------|---------------|
| **Path** | В URL пути | `/items/{id}` | Идентификация ресурса |
| **Query** | После `?` | `?skip=0&limit=10` | Фильтры, пагинация |
| **Body** | В теле запроса | `{"name": "..."}` | Создание/обновление |

### Async/Await - обязательно!

```python
# ✅ Правильно (все примеры используют async)
@app.get("/items")
async def get_items():
    return items

# ❌ Не используется в этом туториале
@app.get("/items")
def get_items():
    return items
```

### Pydantic валидация

```python
# Автоматическая валидация
class Item(BaseModel):
    name: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)

    # Кастомная валидация
    @field_validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Имя не может быть пустым')
        return v
```

## 📝 Задания для практики

1. ✏️ Добавьте endpoint `GET /items/{item_id}/reviews` с query параметром `rating_min`
2. ✏️ Создайте `PATCH /items/{item_id}` для частичного обновления
3. ✏️ Добавьте фильтрацию по диапазону цен: `min_price` и `max_price`
4. ✏️ Реализуйте `POST /items/bulk` для создания нескольких товаров
5. ✏️ Добавьте поиск с `GET /items/search?q=keyword`

## 🐛 Частые ошибки

### 1. Забыли async
```python
# ❌ НЕПРАВИЛЬНО
@app.get("/items")
def get_items():  # Нет async!
    return items

# ✅ ПРАВИЛЬНО
@app.get("/items")
async def get_items():
    return items
```

### 2. Неправильный порядок параметров
```python
# ❌ НЕПРАВИЛЬНО
async def func(name: str = Body(None), item_id: int):
    pass

# ✅ ПРАВИЛЬНО
async def func(item_id: int, name: str = Body(None)):
    pass
```

### 3. Забыли Content-Type
```bash
# ❌ НЕПРАВИЛЬНО
curl -X POST http://localhost:8000/items -d '{"name": "test"}'

# ✅ ПРАВИЛЬНО
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name": "test"}'
```

## 📚 Что дальше?

После изучения этого примера переходите к:
- **Example 02**: Продвинутая Pydantic валидация
- **Example 03**: Интеграция с базой данных (async SQLAlchemy 2.0)
- **Example 04**: Dependency Injection паттерны
- **Example 05**: Полная DDD архитектура

## 🔗 Полезные ссылки

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [HTTP Status Codes](https://httpstatuses.com/)

---

**Совет**: Используйте Swagger UI (`/docs`) для интерактивного тестирования всех endpoints!
