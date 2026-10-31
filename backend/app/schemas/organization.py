from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class OrganizationBase(BaseModel):
    """Base schema for organization attributes."""

    name: str = Field(..., min_length=1, max_length=255, description="Organization display name")
    code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_\-]+$",
        description="Unique URL-friendly code identifier for organization",
    )
    is_active: bool = Field(default=True, description="Whether the organization is active")


class OrganizationCreate(OrganizationBase):
    """Schema for creating a new organization."""
    pass


class OrganizationUpdate(BaseModel):
    """Schema for partially updating an organization."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9_\-]+$")
    is_active: Optional[bool] = None


class OrganizationResponse(OrganizationBase):
    """Schema for serializing organization responses."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
