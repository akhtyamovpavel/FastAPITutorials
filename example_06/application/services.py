"""
Application Layer - Services
Бизнес-логика приложения
"""

from typing import List, Optional
from domain.entities import Product, Order
from domain.repositories import IProductRepository, IOrderRepository
from .dto import (
    ProductCreateDTO, ProductUpdateDTO, ProductResponseDTO,
    OrderCreateDTO, AddItemToOrderDTO, OrderResponseDTO, OrderItemDTO
)


class ProductService:
    """
    Сервис для работы с товарами

    Отвечает за:
    - Оркестрацию бизнес-логики
    - Конвертацию DTO ↔ Entity
    - Вызовы репозиториев
    """

    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo

    def create_product(self, dto: ProductCreateDTO) -> ProductResponseDTO:
        """
        Создание товара

        Workflow:
        1. DTO → Entity (создание с валидацией)
        2. Repository.add (сохранение в БД)
        3. Entity → DTO (ответ клиенту)
        """
        # DTO → Entity
        product = Product(
            name=dto.name,
            price=dto.price,
            quantity=dto.quantity
        )

        # Сохранение через репозиторий
        product = self.product_repo.add(product)

        # Entity → DTO
        return self._to_response_dto(product)

    def get_product(self, product_id: int) -> Optional[ProductResponseDTO]:
        """Получить товар по ID"""
        product = self.product_repo.get(product_id)
        return self._to_response_dto(product) if product else None

    def list_products(self, skip: int = 0, limit: int = 100) -> List[ProductResponseDTO]:
        """Получить список товаров"""
        products = self.product_repo.get_all(skip, limit)
        return [self._to_response_dto(p) for p in products]

    def update_product(self, product_id: int, dto: ProductUpdateDTO) -> Optional[ProductResponseDTO]:
        """
        Обновление товара

        Важно: обновление через Entity методы для сохранения бизнес-правил
        """
        product = self.product_repo.get(product_id)
        if not product:
            return None

        # Обновить через Entity методы (с валидацией)
        if dto.name is not None:
            product.name = dto.name

        if dto.price is not None:
            product.update_price(dto.price)  # Бизнес-правила!

        if dto.quantity is not None:
            diff = dto.quantity - product.quantity
            if diff > 0:
                product.add_stock(diff)
            elif diff < 0:
                product.remove_stock(abs(diff))

        # Сохранить изменения
        product = self.product_repo.update(product)

        return self._to_response_dto(product)

    def delete_product(self, product_id: int) -> bool:
        """Удалить товар"""
        return self.product_repo.delete(product_id)

    def search_products(self, name: str) -> List[ProductResponseDTO]:
        """Поиск товаров по имени"""
        products = self.product_repo.find_by_name(name)
        return [self._to_response_dto(p) for p in products]

    def filter_by_price(self, min_price: float, max_price: float) -> List[ProductResponseDTO]:
        """Фильтр по цене"""
        products = self.product_repo.filter_by_price(min_price, max_price)
        return [self._to_response_dto(p) for p in products]

    def _to_response_dto(self, product: Product) -> ProductResponseDTO:
        """Конвертация Entity → Response DTO"""
        return ProductResponseDTO(
            id=product.id,
            name=product.name,
            price=product.price,
            quantity=product.quantity,
            is_in_stock=product.is_in_stock,
            total_value=product.total_value,
            created_at=product.created_at,
            updated_at=product.updated_at
        )


class OrderService:
    """
    Сервис для работы с заказами

    Оркестрирует взаимодействие Product и Order
    """

    def __init__(
        self,
        order_repo: IOrderRepository,
        product_repo: IProductRepository
    ):
        self.order_repo = order_repo
        self.product_repo = product_repo

    def create_order(self, dto: OrderCreateDTO) -> OrderResponseDTO:
        """Создать пустой заказ"""
        order = Order(user_id=dto.user_id)
        order = self.order_repo.add(order)

        return self._to_response_dto(order)

    def add_item_to_order(
        self,
        order_id: int,
        dto: AddItemToOrderDTO
    ) -> Optional[OrderResponseDTO]:
        """
        Добавить товар в заказ

        Бизнес-логика:
        1. Проверить наличие заказа
        2. Проверить наличие товара
        3. Резервировать товар (Order.add_item с валидацией)
        4. Уменьшить количество на складе
        5. Сохранить изменения
        """
        # Получить заказ
        order = self.order_repo.get(order_id)
        if not order:
            return None

        # Получить товар
        product = self.product_repo.get(dto.product_id)
        if not product:
            raise ValueError(f"Товар с ID {dto.product_id} не найден")

        # Добавить в заказ (с бизнес-правилами)
        order.add_item(product, dto.quantity)

        # Уменьшить количество на складе
        product.remove_stock(dto.quantity)

        # Сохранить изменения
        self.product_repo.update(product)
        order = self.order_repo.update(order)

        return self._to_response_dto(order)

    def get_order(self, order_id: int) -> Optional[OrderResponseDTO]:
        """Получить заказ по ID"""
        order = self.order_repo.get(order_id)
        return self._to_response_dto(order) if order else None

    def get_user_orders(self, user_id: int) -> List[OrderResponseDTO]:
        """Получить заказы пользователя"""
        orders = self.order_repo.get_by_user(user_id)
        return [self._to_response_dto(o) for o in orders]

    def confirm_order(self, order_id: int) -> Optional[OrderResponseDTO]:
        """Подтвердить заказ"""
        order = self.order_repo.get(order_id)
        if not order:
            return None

        order.confirm()  # Бизнес-логика в Entity!
        order = self.order_repo.update(order)

        return self._to_response_dto(order)

    def cancel_order(self, order_id: int) -> Optional[OrderResponseDTO]:
        """
        Отменить заказ

        Бизнес-логика:
        - Вернуть товары на склад
        - Изменить статус заказа
        """
        order = self.order_repo.get(order_id)
        if not order:
            return None

        # Вернуть товары на склад
        for item in order.items:
            product = self.product_repo.get(item.product_id)
            if product:
                product.add_stock(item.quantity)
                self.product_repo.update(product)

        # Отменить заказ
        order.cancel()
        order = self.order_repo.update(order)

        return self._to_response_dto(order)

    def _to_response_dto(self, order: Order) -> OrderResponseDTO:
        """Конвертация Entity → Response DTO"""
        items_dto = [
            OrderItemDTO(
                product_id=item.product_id,
                product_name=item.product_name,
                price=item.price,
                quantity=item.quantity,
                subtotal=item.subtotal
            )
            for item in order.items
        ]

        return OrderResponseDTO(
            id=order.id,
            user_id=order.user_id,
            status=order.status,
            items=items_dto,
            total_amount=order.total_amount,
            items_count=order.items_count,
            created_at=order.created_at
        )
