from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.order import Order, OrderStatus
from app.schemas.order import OrderCreate


def create_order(db: Session, data: OrderCreate) -> Order:
    """Create a new dataset order ensuring customer existence and unique order number."""
    customer = db.get(Customer, data.customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID '{data.customer_id}' does not exist.",
        )

    existing_order = db.scalar(select(Order).where(Order.order_number == data.order_number))
    if existing_order:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Order with number '{data.order_number}' already exists.",
        )

    order = Order(**data.model_dump())
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def get_order(db: Session, order_id: UUID) -> Order:
    """Retrieve an order by its primary key UUID."""
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID '{order_id}' not found.",
        )
    return order


def list_orders(
    db: Session,
    customer_id: Optional[UUID] = None,
    order_status: Optional[OrderStatus] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Order]:
    """Retrieve a paginated list of orders with optional customer and status filters."""
    stmt = select(Order)
    if customer_id is not None:
        stmt = stmt.where(Order.customer_id == customer_id)
    if order_status is not None:
        stmt = stmt.where(Order.status == order_status)
    stmt = stmt.order_by(Order.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def update_order_status(db: Session, order_id: UUID, new_status: OrderStatus) -> Order:
    """Update an order's status."""
    order = get_order(db, order_id)
    order.status = new_status
    db.commit()
    db.refresh(order)
    return order
