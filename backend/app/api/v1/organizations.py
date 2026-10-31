from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)
from app.services import organization_service

router = APIRouter()


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create organization",
)
def create_organization(
    data: OrganizationCreate,
    db: Session = Depends(get_db),
):
    """Register a new customer organization or provider company."""
    return organization_service.create_organization(db=db, data=data)


@router.get(
    "",
    response_model=List[OrganizationResponse],
    summary="List organizations",
)
def list_organizations(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=100, description="Limit for pagination"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
):
    """Retrieve a paginated list of organizations."""
    return organization_service.list_organizations(
        db=db,
        skip=skip,
        limit=limit,
        is_active=is_active,
    )


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Get organization by ID",
)
def get_organization(
    organization_id: UUID,
    db: Session = Depends(get_db),
):
    """Retrieve detailed information for a single organization."""
    return organization_service.get_organization(db=db, org_id=organization_id)


@router.patch(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Update organization",
)
def update_organization(
    organization_id: UUID,
    data: OrganizationUpdate,
    db: Session = Depends(get_db),
):
    """Partially update an organization's details."""
    return organization_service.update_organization(
        db=db,
        org_id=organization_id,
        data=data,
    )


@router.delete(
    "/{organization_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete organization",
)
def delete_organization(
    organization_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete an organization and cascade to its associated resources."""
    organization_service.delete_organization(db=db, org_id=organization_id)
