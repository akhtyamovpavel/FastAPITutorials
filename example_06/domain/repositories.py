"""
Domain Layer - Repository Interfaces
Интерфейсы для работы с хранилищем данных

All methods are ASYNC to support SQLAlchemy 2.0 async operations.
Все методы АСИНХРОННЫЕ для поддержки SQLAlchemy 2.0 async операций.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import Product, Order


class IProductRepository(ABC):
    """
    Repository Interface для Product

    Определяет контракт для работы с товарами
    Реализация находится в infrastructure слое

    ALL METHODS ARE ASYNC / ВСЕ МЕТОДЫ АСИНХРОННЫЕ
    """

    @abstractmethod
    async def add(self, product: Product) -> Product:
        """Добавить новый товар"""
        pass

    @abstractmethod
    async def get(self, product_id: int) -> Optional[Product]:
        """Получить товар по ID"""
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Product]:
        """Получить список товаров"""
        pass

    @abstractmethod
    async def update(self, product: Product) -> Product:
        """Обновить товар"""
        pass

    @abstractmethod
    async def delete(self, product_id: int) -> bool:
        """Удалить товар"""
        pass

    @abstractmethod
    async def find_by_name(self, name: str) -> List[Product]:
        """Найти товары по имени"""
        pass

    @abstractmethod
    async def filter_by_price(self, min_price: float, max_price: float) -> List[Product]:
        """Фильтр по цене"""
        pass


class IOrderRepository(ABC):
    """
    Repository Interface для Order

    ALL METHODS ARE ASYNC / ВСЕ МЕТОДЫ АСИНХРОННЫЕ
    """

    @abstractmethod
    async def add(self, order: Order) -> Order:
        """Создать заказ"""
        pass

    @abstractmethod
    async def get(self, order_id: int) -> Optional[Order]:
        """Получить заказ по ID"""
        pass

    @abstractmethod
    async def get_by_user(self, user_id: int) -> List[Order]:
        """Получить заказы пользователя"""
        pass

    @abstractmethod
    async def update(self, order: Order) -> Order:
        """Обновить заказ"""
        pass

    @abstractmethod
    async def delete(self, order_id: int) -> bool:
        """Удалить заказ"""
        pass
