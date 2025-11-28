"""
Presentation Layer - Routers
HTTP обработчики (контроллеры)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from application.dto import (
    ProductCreateDTO, ProductUpdateDTO, ProductResponseDTO,
    OrderCreateDTO, AddItemToOrderDTO, OrderResponseDTO
)
from application.services import ProductService, OrderService
from application.factories import get_product_service, get_order_service


# ============================================
# Product Router
# ============================================

product_router = APIRouter(prefix="/products", tags=["Products"])


@product_router.post("/", response_model=ProductResponseDTO, status_code=201)
def create_product(
    dto: ProductCreateDTO,
    service: ProductService = Depends(get_product_service)
):
    """
    Создать товар

    Роут делает ТОЛЬКО:
    - Приём HTTP запроса
    - Делегирование бизнес-логики в сервис
    - Возврат HTTP ответа
    """
    return service.create_product(dto)


@product_router.get("/", response_model=List[ProductResponseDTO])
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: ProductService = Depends(get_product_service)
):
    """Получить список товаров с пагинацией"""
    return service.list_products(skip, limit)


@product_router.get("/{product_id}", response_model=ProductResponseDTO)
def get_product(
    product_id: int,
    service: ProductService = Depends(get_product_service)
):
    """Получить товар по ID"""
    product = service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return product


@product_router.put("/{product_id}", response_model=ProductResponseDTO)
def update_product(
    product_id: int,
    dto: ProductUpdateDTO,
    service: ProductService = Depends(get_product_service)
):
    """Обновить товар"""
    product = service.update_product(product_id, dto)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return product


@product_router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    service: ProductService = Depends(get_product_service)
):
    """Удалить товар"""
    success = service.delete_product(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return None


@product_router.get("/search/by-name", response_model=List[ProductResponseDTO])
def search_products(
    name: str = Query(..., min_length=1),
    service: ProductService = Depends(get_product_service)
):
    """Поиск товаров по имени"""
    return service.search_products(name)


@product_router.get("/filter/by-price", response_model=List[ProductResponseDTO])
def filter_products_by_price(
    min_price: float = Query(0, ge=0),
    max_price: float = Query(1000000, ge=0),
    service: ProductService = Depends(get_product_service)
):
    """Фильтрация товаров по цене"""
    return service.filter_by_price(min_price, max_price)


# ============================================
# Order Router
# ============================================

order_router = APIRouter(prefix="/orders", tags=["Orders"])


@order_router.post("/", response_model=OrderResponseDTO, status_code=201)
def create_order(
    dto: OrderCreateDTO,
    service: OrderService = Depends(get_order_service)
):
    """Создать новый заказ"""
    return service.create_order(dto)


@order_router.post("/{order_id}/items", response_model=OrderResponseDTO)
def add_item_to_order(
    order_id: int,
    dto: AddItemToOrderDTO,
    service: OrderService = Depends(get_order_service)
):
    """
    Добавить товар в заказ

    Обработка ошибок:
    - 404: заказ не найден
    - 400: бизнес-ошибки (нет на складе и т.д.)
    """
    try:
        order = service.add_item_to_order(order_id, dto)
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@order_router.get("/{order_id}", response_model=OrderResponseDTO)
def get_order(
    order_id: int,
    service: OrderService = Depends(get_order_service)
):
    """Получить заказ по ID"""
    order = service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return order


@order_router.get("/user/{user_id}", response_model=List[OrderResponseDTO])
def get_user_orders(
    user_id: int,
    service: OrderService = Depends(get_order_service)
):
    """Получить все заказы пользователя"""
    return service.get_user_orders(user_id)


@order_router.post("/{order_id}/confirm", response_model=OrderResponseDTO)
def confirm_order(
    order_id: int,
    service: OrderService = Depends(get_order_service)
):
    """Подтвердить заказ"""
    try:
        order = service.confirm_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@order_router.post("/{order_id}/cancel", response_model=OrderResponseDTO)
def cancel_order(
    order_id: int,
    service: OrderService = Depends(get_order_service)
):
    """Отменить заказ (товары вернутся на склад)"""
    try:
        order = service.cancel_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
