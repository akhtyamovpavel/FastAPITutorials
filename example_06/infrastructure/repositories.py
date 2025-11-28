"""
Infrastructure Layer - Repository Implementations
Реализация репозиториев для работы с БД

SQLAlchemy 2.0 Async Patterns:
- ALL methods are async def
- Use AsyncSession instead of Session
- Use select() instead of query()
- Use result.scalar_one_or_none(), result.scalars().all()
- Use await for all database operations
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from domain.entities import Product, Order, OrderItem
from domain.repositories import IProductRepository, IOrderRepository
from .models import ProductModel, OrderModel, OrderItemModel


class ProductRepository(IProductRepository):
    """
    Async реализация ProductRepository для SQLAlchemy 2.0

    Отвечает за:
    - Маппинг Entity ↔ ORM Model
    - Async CRUD операции с БД
    - Использование современного SQLAlchemy 2.0 API
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_entity(self, model: ProductModel) -> Product:
        """Конвертация ORM Model → Domain Entity"""
        return Product(
            id=model.id,
            name=model.name,
            price=model.price,
            quantity=model.quantity,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _to_model(self, entity: Product) -> ProductModel:
        """Конвертация Domain Entity → ORM Model"""
        return ProductModel(
            id=entity.id,
            name=entity.name,
            price=entity.price,
            quantity=entity.quantity,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

    async def add(self, product: Product) -> Product:
        """Добавить товар (async)"""
        db_product = self._to_model(product)
        self.db.add(db_product)
        await self.db.commit()
        await self.db.refresh(db_product)

        return self._to_entity(db_product)

    async def get(self, product_id: int) -> Optional[Product]:
        """
        Получить товар по ID (async)

        SQLAlchemy 2.0 pattern:
        OLD: self.db.query(ProductModel).filter(ProductModel.id == product_id).first()
        NEW: await self.db.execute(select(ProductModel).where(ProductModel.id == product_id))
        """
        result = await self.db.execute(
            select(ProductModel).where(ProductModel.id == product_id)
        )
        db_product = result.scalar_one_or_none()

        return self._to_entity(db_product) if db_product else None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Product]:
        """
        Получить список товаров (async)

        SQLAlchemy 2.0 pattern:
        OLD: self.db.query(ProductModel).offset(skip).limit(limit).all()
        NEW: await self.db.execute(select(ProductModel).offset(skip).limit(limit))
        """
        result = await self.db.execute(
            select(ProductModel).offset(skip).limit(limit)
        )
        db_products = result.scalars().all()

        return [self._to_entity(p) for p in db_products]

    async def update(self, product: Product) -> Product:
        """
        Обновить товар (async)

        SQLAlchemy 2.0 pattern for fetching before update
        """
        result = await self.db.execute(
            select(ProductModel).where(ProductModel.id == product.id)
        )
        db_product = result.scalar_one_or_none()

        if not db_product:
            raise ValueError(f"Товар с ID {product.id} не найден")

        # Обновить поля
        db_product.name = product.name
        db_product.price = product.price
        db_product.quantity = product.quantity
        db_product.updated_at = product.updated_at

        await self.db.commit()
        await self.db.refresh(db_product)

        return self._to_entity(db_product)

    async def delete(self, product_id: int) -> bool:
        """
        Удалить товар (async)

        SQLAlchemy 2.0 pattern for delete
        """
        result = await self.db.execute(
            select(ProductModel).where(ProductModel.id == product_id)
        )
        db_product = result.scalar_one_or_none()

        if not db_product:
            return False

        await self.db.delete(db_product)
        await self.db.commit()
        return True

    async def find_by_name(self, name: str) -> List[Product]:
        """
        Найти товары по имени (async)

        SQLAlchemy 2.0 pattern:
        OLD: self.db.query(ProductModel).filter(ProductModel.name.contains(name)).all()
        NEW: await self.db.execute(select(ProductModel).where(ProductModel.name.contains(name)))
        """
        result = await self.db.execute(
            select(ProductModel).where(ProductModel.name.contains(name))
        )
        db_products = result.scalars().all()

        return [self._to_entity(p) for p in db_products]

    async def filter_by_price(self, min_price: float, max_price: float) -> List[Product]:
        """
        Фильтр по цене (async)

        SQLAlchemy 2.0 pattern for multiple conditions
        """
        result = await self.db.execute(
            select(ProductModel).where(
                ProductModel.price >= min_price,
                ProductModel.price <= max_price
            )
        )
        db_products = result.scalars().all()

        return [self._to_entity(p) for p in db_products]


class OrderRepository(IOrderRepository):
    """Async реализация OrderRepository для SQLAlchemy 2.0"""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_entity(self, model: OrderModel) -> Order:
        """Конвертация ORM Model → Domain Entity"""
        order = Order(
            id=model.id,
            user_id=model.user_id,
            status=model.status,
            created_at=model.created_at
        )

        # Конвертировать items
        for item_model in model.items:
            order_item = OrderItem(
                product_id=item_model.product_id,
                product_name=item_model.product_name,
                price=item_model.price,
                quantity=item_model.quantity
            )
            order.items.append(order_item)

        return order

    def _to_model(self, entity: Order) -> OrderModel:
        """Конвертация Domain Entity → ORM Model"""
        model = OrderModel(
            id=entity.id,
            user_id=entity.user_id,
            status=entity.status,
            created_at=entity.created_at
        )

        # Конвертировать items
        model.items = [
            OrderItemModel(
                product_id=item.product_id,
                product_name=item.product_name,
                price=item.price,
                quantity=item.quantity
            )
            for item in entity.items
        ]

        return model

    async def add(self, order: Order) -> Order:
        """Создать заказ (async)"""
        db_order = self._to_model(order)
        self.db.add(db_order)
        await self.db.commit()
        await self.db.refresh(db_order)

        return self._to_entity(db_order)

    async def get(self, order_id: int) -> Optional[Order]:
        """
        Получить заказ по ID (async)

        SQLAlchemy 2.0 pattern with relationships
        """
        result = await self.db.execute(
            select(OrderModel).where(OrderModel.id == order_id)
        )
        db_order = result.scalar_one_or_none()

        return self._to_entity(db_order) if db_order else None

    async def get_by_user(self, user_id: int) -> List[Order]:
        """
        Получить заказы пользователя (async)

        SQLAlchemy 2.0 pattern for filtering
        """
        result = await self.db.execute(
            select(OrderModel).where(OrderModel.user_id == user_id)
        )
        db_orders = result.scalars().all()

        return [self._to_entity(o) for o in db_orders]

    async def update(self, order: Order) -> Order:
        """Обновить заказ (async)"""
        result = await self.db.execute(
            select(OrderModel).where(OrderModel.id == order.id)
        )
        db_order = result.scalar_one_or_none()

        if not db_order:
            raise ValueError(f"Заказ с ID {order.id} не найден")

        # Обновить поля
        db_order.status = order.status

        # Удалить старые items
        for item in db_order.items:
            await self.db.delete(item)

        # Добавить новые items
        db_order.items = [
            OrderItemModel(
                product_id=item.product_id,
                product_name=item.product_name,
                price=item.price,
                quantity=item.quantity
            )
            for item in order.items
        ]

        await self.db.commit()
        await self.db.refresh(db_order)

        return self._to_entity(db_order)

    async def delete(self, order_id: int) -> bool:
        """Удалить заказ (async)"""
        result = await self.db.execute(
            select(OrderModel).where(OrderModel.id == order_id)
        )
        db_order = result.scalar_one_or_none()

        if not db_order:
            return False

        await self.db.delete(db_order)
        await self.db.commit()
        return True
