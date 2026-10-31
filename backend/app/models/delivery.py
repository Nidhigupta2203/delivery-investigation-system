import enum
import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.recording import Recording


class DeliveryStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    TRANSFERRING = "TRANSFERRING"
    TRANSFERRED = "TRANSFERRED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class Delivery(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Delivery entity representing a specific delivery attempt/batch for an order."""

    __tablename__ = "deliveries"

    delivery_number: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[DeliveryStatus] = mapped_column(
        SQLEnum(DeliveryStatus, name="delivery_status"),
        default=DeliveryStatus.PLANNED,
        nullable=False,
        index=True,
    )
    source_location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    target_location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decision_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="deliveries",
    )
    recordings: Mapped[List["Recording"]] = relationship(
        "Recording",
        back_populates="delivery",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Delivery number={self.delivery_number} status={self.status}>"
