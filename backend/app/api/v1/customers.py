from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.customer import (
    CustomerCreate,
    CustomerResponse,
    CustomerUpdate,
)
from app.services import customer_service

router = APIRouter()


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create customer",
)
def create_customer(
    data: CustomerCreate,
    db: Session = Depends(get_db),
):
    """Create a new customer user under an organization."""
    return customer_service.create_customer(db=db, data=data)


@router.get(
    "",
    response_model=List[CustomerResponse],
    summary="List customers",
)
def list_customers(
    organization_id: Optional[UUID] = Query(None, description="Filter customers by organization"),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=100, description="Limit for pagination"),
    db: Session = Depends(get_db),
):
    """Retrieve a paginated list of customers."""
    return customer_service.list_customers(
        db=db,
        organization_id=organization_id,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
    summary="Get customer by ID",
)
def get_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
):
    """Retrieve details of a single customer."""
    return customer_service.get_customer(db=db, customer_id=customer_id)


@router.patch(
    "/{customer_id}",
    response_model=CustomerResponse,
    summary="Update customer",
)
def update_customer(
    customer_id: UUID,
    data: CustomerUpdate,
    db: Session = Depends(get_db),
):
    """Partially update a customer's profile."""
    return customer_service.update_customer(
        db=db,
        customer_id=customer_id,
        data=data,
    )


@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete customer",
)
def delete_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a customer and their orders."""
    customer_service.delete_customer(db=db, customer_id=customer_id)
