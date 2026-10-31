from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.delivery import DeliveryStatus
from app.schemas.delivery import (
    DeliveryCreate,
    DeliveryResponse,
    DeliveryStatusUpdate,
)
from app.services import delivery_service

router = APIRouter()


@router.post(
    "",
    response_model=DeliveryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create delivery",
)
def create_delivery(
    data: DeliveryCreate,
    db: Session = Depends(get_db),
):
    """Create a new delivery batch for an existing order."""
    return delivery_service.create_delivery(db=db, data=data)


@router.get(
    "",
    response_model=List[DeliveryResponse],
    summary="List deliveries",
)
def list_deliveries(
    order_id: Optional[UUID] = Query(None, description="Filter deliveries by order"),
    delivery_status: Optional[DeliveryStatus] = Query(None, alias="status", description="Filter deliveries by status"),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=100, description="Limit for pagination"),
    db: Session = Depends(get_db),
):
    """Retrieve a paginated list of deliveries with optional order and status filters."""
    return delivery_service.list_deliveries(
        db=db,
        order_id=order_id,
        delivery_status=delivery_status,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{delivery_id}",
    response_model=DeliveryResponse,
    summary="Get delivery by ID",
)
def get_delivery(
    delivery_id: UUID,
    db: Session = Depends(get_db),
):
    """Retrieve details and review status of a specific delivery."""
    return delivery_service.get_delivery(db=db, delivery_id=delivery_id)


@router.patch(
    "/{delivery_id}/status",
    response_model=DeliveryResponse,
    summary="Update delivery status",
)
def update_delivery_status(
    delivery_id: UUID,
    data: DeliveryStatusUpdate,
    db: Session = Depends(get_db),
):
    """Update a delivery's lifecycle state or customer acceptance/rejection review."""
    return delivery_service.update_delivery_status(
        db=db,
        delivery_id=delivery_id,
        data=data,
    )
