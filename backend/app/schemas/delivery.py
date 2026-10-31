from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.models.delivery import DeliveryStatus


class DeliveryBase(BaseModel):
    """Base schema for delivery attributes."""

    order_id: UUID = Field(..., description="UUID of the order this delivery belongs to")
    delivery_number: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Delivery batch identifier (e.g. DEL-001)",
    )
    source_location: Optional[str] = Field(
        None,
        max_length=500,
        description="Source storage path or bucket URI",
    )
    target_location: Optional[str] = Field(
        None,
        max_length=500,
        description="Customer target storage path or bucket URI",
    )


class DeliveryCreate(DeliveryBase):
    """Schema for creating a new delivery."""
    pass


class DeliveryStatusUpdate(BaseModel):
    """Schema for updating a delivery's lifecycle or review status."""

    status: DeliveryStatus = Field(..., description="New delivery status")
    rejection_reason: Optional[str] = Field(
        None,
        max_length=2000,
        description="Reason for rejection (required if status is REJECTED)",
    )
    decision_notes: Optional[str] = Field(
        None,
        max_length=2000,
        description="Optional notes from the investigation or review decision",
    )


class DeliveryResponse(DeliveryBase):
    """Schema for serializing delivery responses."""

    id: UUID
    status: DeliveryStatus
    rejection_reason: Optional[str]
    decision_notes: Optional[str]
    accepted_at: Optional[datetime]
    rejected_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
