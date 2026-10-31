import enum
import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Enum as SQLEnum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.delivery import Delivery


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"


class Order(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Order entity for requesting robotics dataset recordings."""

    __tablename__ = "orders"

    order_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus, name="order_status"),
        default=OrderStatus.PENDING,
        nullable=False,
        index=True,
    )
    requested_recordings_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    customer: Mapped["Customer"] = relationship(
        "Customer",
        back_populates="orders",
    )
    deliveries: Mapped[List["Delivery"]] = relationship(
        "Delivery",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Order number={self.order_number} status={self.status}>"
