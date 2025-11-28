# Example 02: Pydantic + BaseModel
# Pydantic Validation and Data Models

**[🇬🇧 English version](README.md)**

## 📚 Что изучаем

В этом примере разбираем продвинутую валидацию с Pydantic v2:
- ✅ BaseModel и структурированные данные
- ✅ Валидация полей через `Field()` и `@field_validator`
- ✅ Вложенные модели (nested models)
- ✅ Enum для ограничения значений
- ✅ ConfigDict для настройки моделей (Pydantic v2)
- ✅ Разделение моделей: Create, Update, Response, InDB
- ✅ **Все примеры в ОДНОМ файле** (main.py)
- ✅ **Все endpoints асинхронные** (async/await)

## 🚀 Как запустить

```bash
# Установить зависимости
pip install fastapi uvicorn pydantic[email]

# Запустить сервер
cd example_02
uvicorn main:app --reload
```

Документация API: `http://localhost:8000/docs`

## 🎯 Зачем нужен Pydantic?

### Без Pydantic (Example 01):
```python
@app.post("/items")
async def create_item(
    name: str = Body(...),
    price: float = Body(...),
    description: str = Body(None),
    category: str = Body(...),
    tags: list = Body([])
):
    # 😰 Много параметров!
    # 😰 Валидация размазана по коду
    # 😰 Сложно читать и поддерживать
    pass
```

### С Pydantic:
```python
class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    description: str | None = None
    category: str
    tags: list[str] = []

@app.post("/items")
async def create_item(item: ItemCreate):
    # ✅ Чисто, понятно
    # ✅ Валидация в модели
    # ✅ Автодополнение в IDE
    pass
```

## 🔍 Разбор примеров

### 1. Базовая модель

```python
from pydantic import BaseModel

class User(BaseModel):
    username: str
    email: str
    age: int | None = None  # Опционально (Python 3.10+)
```

**Использование:**
```python
# Создание
user = User(username="john", email="john@example.com", age=25)

# Валидация
user = User(username="john", email="john@example.com", age="invalid")
# ❌ ValidationError: age должен быть int
```

---

### 2. Field() - продвинутая валидация

```python
from pydantic import Field, EmailStr

class Product(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0, le=1000000)
    sku: str = Field(..., pattern=r'^[A-Z]{3}-\d{6}$')
    email: EmailStr  # Автоматическая валидация email
```

**Валидаторы Field:**
- `min_length`, `max_length` - для строк
- `gt`, `ge`, `lt`, `le` - для чисел
- `pattern` - regex для строк
- `max_items` - для списков

**Тестирование:**
```bash
curl -X POST http://localhost:8000/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ноутбук",
    "price": 50000,
    "sku": "LAP-123456",
    "quantity": 10
  }'
```

---

### 3. Enum для ограниченного набора значений

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
    status: OrderStatus  # Только значения из Enum!
```

**Преимущества:**
- IDE автодополняет возможные значения
- Защита от опечаток
- Автоматическая документация в Swagger

**Тестирование:**
```bash
# ✅ Правильно
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"order_id": 1, "status": "pending", "items": ["item1"], "total": 1000}'

# ❌ Неправильно
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"order_id": 1, "status": "invalid", "items": ["item1"], "total": 1000}'
# Ошибка: status должен быть одним из: pending, processing, shipped, delivered, cancelled
```

---

### 4. Кастомные валидаторы (Pydantic v2)

```python
from pydantic import field_validator, model_validator

class User(BaseModel):
    username: str
    password: str
    age: int | None = None

    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        """Валидация на уровне поля"""
        if not v.replace('_', '').isalnum():
            raise ValueError('Только буквы, цифры и _')
        return v

    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Проверка сложности пароля"""
        if len(v) < 8:
            raise ValueError('Минимум 8 символов')
        if not any(char.isdigit() for char in v):
            raise ValueError('Нужна хотя бы одна цифра')
        if not any(char.isupper() for char in v):
            raise ValueError('Нужна заглавная буква')
        return v

    @model_validator(mode='after')
    def check_age_restriction(self) -> 'User':
        """Валидация на уровне модели"""
        if self.age is not None and self.age < 18:
            raise ValueError('Только 18+')
        return self
```

**Важно (Pydantic v2):**
- Используем `@field_validator` вместо старого `@validator`
- Обязательно добавляем `@classmethod`
- `@model_validator` для валидации всей модели

---

### 5. Вложенные модели

```python
class Address(BaseModel):
    street: str
    city: str
    postal_code: str
    country: str = "Россия"

class ContactInfo(BaseModel):
    email: EmailStr
    phone: str = Field(..., pattern=r'^\+?\d{10,15}$')

class UserProfile(BaseModel):
    name: str
    contact: ContactInfo      # Вложенная модель!
    address: Address | None = None  # Опциональная вложенная
```

**Тестирование:**
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
        "street": "Ленина 1",
        "city": "Москва",
        "postal_code": "123456"
      }
    }
  }'
```

---

### 6. ConfigDict - настройка моделей (Pydantic v2)

```python
from pydantic import ConfigDict

class User(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,    # Убирать пробелы из строк
        validate_assignment=True,      # Валидация при изменении
        extra='forbid',                # Запретить лишние поля
        from_attributes=True           # Для ORM (было orm_mode)
    )

    username: str
    email: EmailStr
```

**Важные изменения в Pydantic v2:**
- `orm_mode = True` → `from_attributes=True`
- `class Config` → `model_config = ConfigDict()`
- Более строгая валидация по умолчанию

---

### 7. Разделение моделей: Create, Update, Response, InDB

```python
# Базовая модель с общими полями
class ItemBase(BaseModel):
    name: str
    price: float

# Для создания - входные данные от клиента
class ItemCreate(ItemBase):
    description: str | None = None
    quantity: int = 1

# Для обновления - все поля опциональные
class ItemUpdate(BaseModel):
    name: str | None = None
    price: float | None = Field(None, gt=0)
    description: str | None = None
    quantity: int | None = Field(None, ge=0)

# Для ответа API - добавляем автогенерируемые поля
class ItemResponse(ItemBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Для хранения в БД - может содержать служебные поля
class ItemInDB(ItemResponse):
    hashed_password: str | None = None
    is_deleted: bool = False
```

**Зачем разделять?**

1. **ItemCreate** - что принимаем от клиента
   ```python
   @app.post("/items")
   async def create(item: ItemCreate):
       pass
   ```

2. **ItemUpdate** - для частичного обновления
   ```python
   @app.patch("/items/{id}")
   async def update(id: int, item: ItemUpdate):
       # Обновляем только переданные поля
       update_data = item.model_dump(exclude_unset=True)
       pass
   ```

3. **ItemResponse** - что возвращаем клиенту (скрываем служебные поля)
   ```python
   @app.get("/items/{id}", response_model=ItemResponse)
   async def get(id: int):
       return db_item  # hashed_password не попадёт в ответ!
   ```

4. **ItemInDB** - полная модель для работы с БД

---

## 📊 Полезные методы Pydantic v2

```python
item = Item(name="Товар", price=100)

# Конвертация в словарь (Pydantic v2)
item.model_dump()
# {'name': 'Товар', 'price': 100, 'description': None}

# Только заполненные поля
item.model_dump(exclude_unset=True)
# {'name': 'Товар', 'price': 100}

# Исключить определённые поля
item.model_dump(exclude={'description'})

# JSON строка
item.model_dump_json()

# Создать из словаря
item = Item.model_validate({'name': 'Товар', 'price': 100})
```

**Важные изменения в Pydantic v2:**
- `.dict()` → `.model_dump()`
- `.json()` → `.model_dump_json()`
- `.parse_obj()` → `.model_validate()`

## 🎯 Ключевые концепции

### Асинхронные endpoints - обязательно!

```python
# ✅ Все примеры используют async
@app.post("/items")
async def create_item(item: ItemCreate):
    return item

# ❌ НЕ используется
@app.post("/items")
def create_item(item: ItemCreate):
    return item
```

### Pydantic v2 vs v1

| v1 (старое) | v2 (новое, используем) |
|-------------|------------------------|
| `@validator` | `@field_validator` |
| `class Config` | `model_config = ConfigDict()` |
| `orm_mode = True` | `from_attributes=True` |
| `.dict()` | `.model_dump()` |
| `.json()` | `.model_dump_json()` |

## 📝 Задания для практики

1. ✏️ Создайте модель `Book` с валидацией ISBN формата
2. ✏️ Реализуйте систему комментариев с вложенными моделями `Comment` и `Author`
3. ✏️ Добавьте кастомный валидатор для проверки возраста (18+)
4. ✏️ Создайте API для блога с `PostCreate`, `PostUpdate`, `PostResponse`
5. ✏️ Используйте Enum для статуса поста (`draft`, `published`, `archived`)

## 🐛 Частые ошибки

### 1. Используете Pydantic v1 синтаксис

```python
# ❌ НЕПРАВИЛЬНО (Pydantic v1)
class User(BaseModel):
    class Config:
        orm_mode = True

    @validator('username')
    def check_username(cls, v):
        return v

# ✅ ПРАВИЛЬНО (Pydantic v2)
class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_validator('username')
    @classmethod
    def check_username(cls, v):
        return v
```

### 2. Забыли exclude_unset для PATCH

```python
# ❌ НЕПРАВИЛЬНО - все поля станут None
update_data = item_update.model_dump()

# ✅ ПРАВИЛЬНО - только переданные поля
update_data = item_update.model_dump(exclude_unset=True)
```

### 3. Не установили зависимости

```bash
pip install email-validator  # для EmailStr
pip install pydantic[email]  # или так
```

## 🔗 Следующий шаг

Переходите к **Example 03**, где интегрируем **async SQLAlchemy 2.0** и научимся работать с базой данных!

**Важные темы Example 03:**
- Async database operations
- Использование `db.execute(select(...))` вместо `db.query()`
- `mapped_column` и `Mapped[type]` вместо `Column`
- **Ключевая концепция: Schema (Pydantic) vs Model (SQLAlchemy)**

---

**Совет**: Все примеры в этом файле используют Pydantic v2 и async/await!
