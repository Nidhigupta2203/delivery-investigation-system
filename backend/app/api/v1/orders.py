from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.order import OrderStatus
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderStatusUpdate,
)
from app.services import order_service

router = APIRouter()


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create order",
)
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
):
    """Place a new robotics dataset recording order."""
    return order_service.create_order(db=db, data=data)


@router.get(
    "",
    response_model=List[OrderResponse],
    summary="List orders",
)
def list_orders(
    customer_id: Optional[UUID] = Query(None, description="Filter orders by customer"),
    order_status: Optional[OrderStatus] = Query(None, alias="status", description="Filter orders by lifecycle status"),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=100, description="Limit for pagination"),
    db: Session = Depends(get_db),
):
    """Retrieve a paginated list of orders with optional customer and status filters."""
    return order_service.list_orders(
        db=db,
        customer_id=customer_id,
        order_status=order_status,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order by ID",
)
def get_order(
    order_id: UUID,
    db: Session = Depends(get_db),
):
    """Retrieve details of a specific order."""
    return order_service.get_order(db=db, order_id=order_id)


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Update order status",
)
def update_order_status(
    order_id: UUID,
    data: OrderStatusUpdate,
    db: Session = Depends(get_db),
):
    """Update the fulfillment or lifecycle status of an order."""
    return order_service.update_order_status(
        db=db,
        order_id=order_id,
        new_status=data.status,
    )
