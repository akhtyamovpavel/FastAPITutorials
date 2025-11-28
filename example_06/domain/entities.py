"""
Domain Layer - Entities
Сущности предметной области (бизнес-объекты)
"""

from datetime import datetime
from typing import Optional


class Product:
    """
    Entity - Сущность товара

    Характеристики Entity:
    - Имеет уникальный идентификатор (id)
    - Содержит бизнес-логику
    - Не зависит от БД или фреймворка
    """

    def __init__(
        self,
        name: str,
        price: float,
        quantity: int,
        id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.name = name
        self._price = price  # Приватное поле
        self._quantity = quantity
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

        # Валидация при создании
        self._validate()

    def _validate(self):
        """Бизнес-правила валидации"""
        if not self.name or len(self.name) < 3:
            raise ValueError("Название должно быть минимум 3 символа")

        if self._price <= 0:
            raise ValueError("Цена должна быть положительной")

        if self._quantity < 0:
            raise ValueError("Количество не может быть отрицательным")

    @property
    def price(self) -> float:
        """Цена товара"""
        return self._price

    def update_price(self, new_price: float) -> None:
        """
        Обновление цены с бизнес-правилами

        Бизнес-правило: цена не может измениться более чем на 50%
        """
        if new_price <= 0:
            raise ValueError("Цена должна быть положительной")

        price_change_percent = abs(new_price - self._price) / self._price
        if price_change_percent > 0.5:
            raise ValueError("Цена не может измениться более чем на 50% за раз")

        self._price = new_price
        self.updated_at = datetime.utcnow()

    @property
    def quantity(self) -> int:
        """Количество на складе"""
        return self._quantity

    def add_stock(self, amount: int) -> None:
        """Добавить товар на склад"""
        if amount <= 0:
            raise ValueError("Количество должно быть положительным")

        self._quantity += amount
        self.updated_at = datetime.utcnow()

    def remove_stock(self, amount: int) -> None:
        """Убрать товар со склада"""
        if amount <= 0:
            raise ValueError("Количество должно быть положительным")

        if self._quantity < amount:
            raise ValueError(f"Недостаточно товара на складе. Доступно: {self._quantity}")

        self._quantity -= amount
        self.updated_at = datetime.utcnow()

    @property
    def is_in_stock(self) -> bool:
        """Есть ли товар в наличии"""
        return self._quantity > 0

    @property
    def total_value(self) -> float:
        """Общая стоимость товара на складе"""
        return self._price * self._quantity

    def __repr__(self):
        return f"Product(id={self.id}, name='{self.name}', price={self._price}, quantity={self._quantity})"


class Order:
    """
    Entity - Заказ

    Агрегат, который управляет товарными позициями
    """

    def __init__(
        self,
        user_id: int,
        id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        status: str = "pending"
    ):
        self.id = id
        self.user_id = user_id
        self.status = status
        self.items: list[OrderItem] = []
        self.created_at = created_at or datetime.utcnow()

    def add_item(self, product: Product, quantity: int) -> None:
        """
        Добавить товар в заказ

        Бизнес-логика:
        - Проверка наличия на складе
        - Резервирование товара
        """
        if quantity <= 0:
            raise ValueError("Количество должно быть положительным")

        if not product.is_in_stock:
            raise ValueError(f"Товар '{product.name}' отсутствует на складе")

        if product.quantity < quantity:
            raise ValueError(
                f"Недостаточно товара '{product.name}'. "
                f"Доступно: {product.quantity}, запрошено: {quantity}"
            )

        # Найти существующую позицию
        for item in self.items:
            if item.product_id == product.id:
                item.quantity += quantity
                return

        # Создать новую позицию
        item = OrderItem(
            product_id=product.id,
            product_name=product.name,
            price=product.price,
            quantity=quantity
        )
        self.items.append(item)

    def remove_item(self, product_id: int) -> None:
        """Удалить товар из заказа"""
        self.items = [item for item in self.items if item.product_id != product_id]

    @property
    def total_amount(self) -> float:
        """Общая сумма заказа"""
        return sum(item.subtotal for item in self.items)

    @property
    def items_count(self) -> int:
        """Количество позиций в заказе"""
        return len(self.items)

    def confirm(self) -> None:
        """Подтвердить заказ"""
        if not self.items:
            raise ValueError("Заказ пуст")

        if self.status != "pending":
            raise ValueError("Можно подтвердить только заказ в статусе pending")

        self.status = "confirmed"

    def cancel(self) -> None:
        """Отменить заказ"""
        if self.status in ["delivered", "cancelled"]:
            raise ValueError(f"Нельзя отменить заказ в статусе {self.status}")

        self.status = "cancelled"

    def __repr__(self):
        return (f"Order(id={self.id}, user_id={self.user_id}, "
                f"status='{self.status}', items={self.items_count})")


class OrderItem:
    """
    Value Object - Товарная позиция заказа

    Характеристики Value Object:
    - Не имеет идентификатора
    - Неизменяемый (immutable)
    - Определяется значениями полей
    """

    def __init__(
        self,
        product_id: int,
        product_name: str,
        price: float,
        quantity: int
    ):
        self._product_id = product_id
        self._product_name = product_name
        self._price = price
        self._quantity = quantity

    @property
    def product_id(self) -> int:
        return self._product_id

    @property
    def product_name(self) -> str:
        return self._product_name

    @property
    def price(self) -> float:
        return self._price

    @property
    def quantity(self) -> int:
        return self._quantity

    @property
    def subtotal(self) -> float:
        """Стоимость позиции"""
        return self._price * self._quantity

    def __eq__(self, other):
        """Value Objects сравниваются по значению"""
        if not isinstance(other, OrderItem):
            return False
        return (
            self._product_id == other._product_id and
            self._price == other._price and
            self._quantity == other._quantity
        )

    def __repr__(self):
        return (f"OrderItem(product_id={self._product_id}, "
                f"name='{self._product_name}', quantity={self._quantity})")
