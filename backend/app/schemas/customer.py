from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class CustomerBase(BaseModel):
    """Base schema for customer attributes."""

    organization_id: UUID = Field(..., description="UUID of the parent organization")
    name: str = Field(..., min_length=1, max_length=255, description="Customer name")
    email: str = Field(
        ...,
        min_length=5,
        max_length=255,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        description="Valid customer email address",
    )
    is_active: bool = Field(default=True, description="Whether the customer account is active")


class CustomerCreate(CustomerBase):
    """Schema for creating a new customer."""
    pass


class CustomerUpdate(BaseModel):
    """Schema for partially updating a customer."""

    organization_id: Optional[UUID] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(
        None,
        min_length=5,
        max_length=255,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )
    is_active: Optional[bool] = None


class CustomerResponse(CustomerBase):
    """Schema for serializing customer responses."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
