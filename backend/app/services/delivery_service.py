from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.delivery import Delivery, DeliveryStatus
from app.models.order import Order
from app.schemas.delivery import DeliveryCreate, DeliveryStatusUpdate


def create_delivery(db: Session, data: DeliveryCreate) -> Delivery:
    """Create a new delivery batch tied to an existing order."""
    order = db.get(Order, data.order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parent order with ID '{data.order_id}' does not exist.",
        )

    delivery = Delivery(**data.model_dump())
    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    return delivery


def get_delivery(db: Session, delivery_id: UUID) -> Delivery:
    """Retrieve a delivery by its primary key UUID."""
    delivery = db.get(Delivery, delivery_id)
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery with ID '{delivery_id}' not found.",
        )
    return delivery


def list_deliveries(
    db: Session,
    order_id: Optional[UUID] = None,
    delivery_status: Optional[DeliveryStatus] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Delivery]:
    """Retrieve a paginated list of deliveries with optional order and status filters."""
    stmt = select(Delivery)
    if order_id is not None:
        stmt = stmt.where(Delivery.order_id == order_id)
    if delivery_status is not None:
        stmt = stmt.where(Delivery.status == delivery_status)
    stmt = stmt.order_by(Delivery.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def update_delivery_status(
    db: Session,
    delivery_id: UUID,
    data: DeliveryStatusUpdate,
) -> Delivery:
    """Update a delivery's lifecycle or review status with business domain validation."""
    delivery = get_delivery(db, delivery_id)

    # Validate rejection requires a non-empty reason
    if data.status == DeliveryStatus.REJECTED:
        if not data.rejection_reason or not data.rejection_reason.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A rejection reason must be provided when rejecting a delivery.",
            )
        delivery.rejection_reason = data.rejection_reason.strip()
        delivery.rejected_at = datetime.now(timezone.utc)

    elif data.status == DeliveryStatus.ACCEPTED:
        delivery.accepted_at = datetime.now(timezone.utc)

    delivery.status = data.status

    if data.decision_notes is not None:
        delivery.decision_notes = data.decision_notes

    db.commit()
    db.refresh(delivery)
    return delivery
