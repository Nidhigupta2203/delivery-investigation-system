from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.models.order import OrderStatus


class OrderBase(BaseModel):
    """Base schema for order attributes."""

    customer_id: UUID = Field(..., description="UUID of the customer placing the order")
    order_number: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique business identifier for the order (e.g. ORD-2026-001)",
    )
    requested_recordings_count: int = Field(
        default=0,
        ge=0,
        description="Number of recordings requested in this order",
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Optional notes or specifications for the dataset order",
    )


class OrderCreate(OrderBase):
    """Schema for creating a new order."""
    pass


class OrderStatusUpdate(BaseModel):
    """Schema for updating an order's status."""

    status: OrderStatus = Field(..., description="New status for the order")


class OrderResponse(OrderBase):
    """Schema for serializing order responses."""

    id: UUID
    status: OrderStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
