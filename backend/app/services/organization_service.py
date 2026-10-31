from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationUpdate


def create_organization(db: Session, data: OrganizationCreate) -> Organization:
    """Create a new organization ensuring unique code identifier."""
    existing = db.scalar(select(Organization).where(Organization.code == data.code))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Organization with code '{data.code}' already exists.",
        )

    org = Organization(**data.model_dump())
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def get_organization(db: Session, org_id: UUID) -> Organization:
    """Retrieve an organization by its primary key UUID."""
    org = db.get(Organization, org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization with ID '{org_id}' not found.",
        )
    return org


def list_organizations(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
) -> List[Organization]:
    """Retrieve a paginated list of organizations with optional activity filter."""
    stmt = select(Organization)
    if is_active is not None:
        stmt = stmt.where(Organization.is_active == is_active)
    stmt = stmt.order_by(Organization.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def update_organization(
    db: Session,
    org_id: UUID,
    data: OrganizationUpdate,
) -> Organization:
    """Partially update an existing organization."""
    org = get_organization(db, org_id)
    update_data = data.model_dump(exclude_unset=True)

    if "code" in update_data and update_data["code"] != org.code:
        existing = db.scalar(
            select(Organization).where(
                Organization.code == update_data["code"],
                Organization.id != org_id,
            )
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Organization with code '{update_data['code']}' already exists.",
            )

    for field, value in update_data.items():
        setattr(org, field, value)

    db.commit()
    db.refresh(org)
    return org


def delete_organization(db: Session, org_id: UUID) -> None:
    """Delete an organization and its associated entities."""
    org = get_organization(db, org_id)
    db.delete(org)
    db.commit()
