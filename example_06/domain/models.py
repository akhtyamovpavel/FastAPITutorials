"""
Domain Models (Entities) / Доменные модели (сущности)

This layer represents business entities and their relationships.
Этот слой представляет бизнес-сущности и их отношения.

WHY? / ЗАЧЕМ?
- Encapsulate business rules / Инкапсулировать бизнес-правила
- Represent real-world concepts / Представлять реальные концепции
- Independent of database details / Независимы от деталей БД

SQLAlchemy 2.0 Features / Возможности SQLAlchemy 2.0:
- mapped_column instead of Column / mapped_column вместо Column
- Mapped[type] for type hints / Mapped[type] для подсказок типов
- Better IDE support / Лучшая поддержка IDE
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class User(Base):
    """
    User entity / Сущность пользователя

    Represents a user in the system with all business attributes.
    Представляет пользователя в системе со всеми бизнес-атрибутами.

    Domain Rules / Доменные правила:
    - Email must be unique / Email должен быть уникальным
    - Username must be unique / Имя пользователя должно быть уникальным
    - Users can be active or inactive / Пользователи могут быть активны или неактивны
    """

    __tablename__ = "users"

    # Primary key / Первичный ключ
    # Mapped[int] tells IDE this is an integer
    # Mapped[int] говорит IDE, что это целое число
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Business attributes / Бизнес-атрибуты
    # mapped_column(String(100)) creates VARCHAR(100) column
    # mapped_column(String(100)) создает колонку VARCHAR(100)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Status flag / Флаг статуса
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamps / Временные метки
    # server_default=func.now() uses database function for timestamp
    # server_default=func.now() использует функцию БД для временной метки
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        """String representation for debugging / Строковое представление для отладки"""
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

    # Business methods can go here / Бизнес-методы могут быть здесь
    def activate(self) -> None:
        """Activate user / Активировать пользователя"""
        self.is_active = True

    def deactivate(self) -> None:
        """Deactivate user / Деактивировать пользователя"""
        self.is_active = False
