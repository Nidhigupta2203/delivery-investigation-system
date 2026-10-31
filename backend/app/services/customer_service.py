from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.organization import Organization
from app.schemas.customer import CustomerCreate, CustomerUpdate


def create_customer(db: Session, data: CustomerCreate) -> Customer:
    """Create a new customer ensuring organization existence and unique email."""
    org = db.get(Organization, data.organization_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parent organization with ID '{data.organization_id}' does not exist.",
        )

    existing_email = db.scalar(select(Customer).where(Customer.email == data.email))
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Customer with email '{data.email}' already exists.",
        )

    customer = Customer(**data.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def get_customer(db: Session, customer_id: UUID) -> Customer:
    """Retrieve a customer by their primary key UUID."""
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID '{customer_id}' not found.",
        )
    return customer


def list_customers(
    db: Session,
    organization_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Customer]:
    """Retrieve a paginated list of customers with optional organization filter."""
    stmt = select(Customer)
    if organization_id is not None:
        stmt = stmt.where(Customer.organization_id == organization_id)
    stmt = stmt.order_by(Customer.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def update_customer(
    db: Session,
    customer_id: UUID,
    data: CustomerUpdate,
) -> Customer:
    """Partially update an existing customer."""
    customer = get_customer(db, customer_id)
    update_data = data.model_dump(exclude_unset=True)

    if "organization_id" in update_data and update_data["organization_id"] != customer.organization_id:
        org = db.get(Organization, update_data["organization_id"])
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent organization with ID '{update_data['organization_id']}' does not exist.",
            )

    if "email" in update_data and update_data["email"] != customer.email:
        existing_email = db.scalar(
            select(Customer).where(
                Customer.email == update_data["email"],
                Customer.id != customer_id,
            )
        )
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Customer with email '{update_data['email']}' already exists.",
            )

    for field, value in update_data.items():
        setattr(customer, field, value)

    db.commit()
    db.refresh(customer)
    return customer


def delete_customer(db: Session, customer_id: UUID) -> None:
    """Delete a customer and their cascading orders/deliveries."""
    customer = get_customer(db, customer_id)
    db.delete(customer)
    db.commit()
