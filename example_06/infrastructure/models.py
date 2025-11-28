"""
Infrastructure Layer - ORM Models
Модели SQLAlchemy для БД

SQLAlchemy 2.0 Modern Syntax:
- Use mapped_column() instead of Column()
- Use Mapped[type] type hints for type safety
- Import Base from root database.py (async-compliant)
"""

from typing import Optional
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Import Base from root database.py (async version)
from database import Base


class ProductModel(Base):
    """ORM Model для Product with SQLAlchemy 2.0 syntax"""
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    quantity: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class OrderModel(Base):
    """ORM Model для Order with SQLAlchemy 2.0 syntax"""
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Связь с items
    items: Mapped[list["OrderItemModel"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItemModel(Base):
    """ORM Model для OrderItem with SQLAlchemy 2.0 syntax"""
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(nullable=False)
    product_name: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)

    # Связь с order
    order: Mapped["OrderModel"] = relationship(back_populates="items")
