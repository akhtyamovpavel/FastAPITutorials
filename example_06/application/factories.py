"""
Application Layer - Factories
Фабрики для создания сервисов с инжекцией зависимостей

Updated for SQLAlchemy 2.0 async:
- Use AsyncSession instead of Session
- Import get_session from root database.py (async version)
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from infrastructure.repositories import ProductRepository, OrderRepository
from .services import ProductService, OrderService


def get_product_service(db: AsyncSession = Depends(get_session)) -> ProductService:
    """
    Factory для ProductService

    Используется FastAPI DI для автоматического создания сервиса
    Now uses AsyncSession for async database operations
    """
    product_repo = ProductRepository(db)
    return ProductService(product_repo)


def get_order_service(db: AsyncSession = Depends(get_session)) -> OrderService:
    """
    Factory для OrderService

    Инжектирует оба репозитория
    Now uses AsyncSession for async database operations
    """
    product_repo = ProductRepository(db)
    order_repo = OrderRepository(db)
    return OrderService(order_repo, product_repo)
