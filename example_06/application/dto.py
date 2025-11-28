"""
Application Layer - DTOs (Data Transfer Objects)
Объекты для передачи данных между слоями
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ============================================
# Product DTOs
# ============================================

class ProductCreateDTO(BaseModel):
    """DTO для создания товара"""
    name: str = Field(..., min_length=3, max_length=200)
    price: float = Field(..., gt=0)
    quantity: int = Field(default=0, ge=0)


class ProductUpdateDTO(BaseModel):
    """DTO для обновления товара"""
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    price: Optional[float] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=0)


class ProductResponseDTO(BaseModel):
    """DTO для ответа с товаром"""
    id: int
    name: str
    price: float
    quantity: int
    is_in_stock: bool
    total_value: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Замена orm_mode в Pydantic v2


# ============================================
# Order DTOs
# ============================================

class OrderItemDTO(BaseModel):
    """DTO для товарной позиции"""
    product_id: int
    product_name: str
    price: float
    quantity: int
    subtotal: float


class OrderCreateDTO(BaseModel):
    """DTO для создания заказа"""
    user_id: int


class AddItemToOrderDTO(BaseModel):
    """DTO для добавления товара в заказ"""
    product_id: int
    quantity: int = Field(..., gt=0)


class OrderResponseDTO(BaseModel):
    """DTO для ответа с заказом"""
    id: int
    user_id: int
    status: str
    items: List[OrderItemDTO]
    total_amount: float
    items_count: int
    created_at: datetime

    class Config:
        from_attributes = True
