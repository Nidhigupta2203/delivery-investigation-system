from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.delivery import DeliveryStatus
from app.schemas.comparison import DeliveryComparisonResponse
from app.schemas.delivery import (
    DeliveryCreate,
    DeliveryResponse,
    DeliveryStatusUpdate,
)
from app.schemas.manifest import (
    ManifestCreate,
    ManifestResponse,
)
from app.schemas.transfer import (
    TransferJobResponse,
)
from app.services import (
    comparison_service,
    delivery_service,
    manifest_service,
    transfer_service,
)

router = APIRouter()


# --- Standard Delivery CRUD ---


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


# --- Manifest APIs ---


@router.post(
    "/{delivery_id}/manifest",
    response_model=ManifestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register delivery manifest",
)
def register_manifest(
    delivery_id: UUID,
    data: ManifestCreate,
    db: Session = Depends(get_db),
):
    """Register or replace recording items in a delivery manifest."""
    return manifest_service.register_manifest(
        db=db,
        delivery_id=delivery_id,
        data=data,
    )


@router.get(
    "/{delivery_id}/manifest",
    response_model=ManifestResponse,
    summary="Inspect delivery manifest",
)
def get_manifest(
    delivery_id: UUID,
    db: Session = Depends(get_db),
):
    """Inspect the recorded manifest files, checksums, and quality status."""
    return manifest_service.get_manifest(
        db=db,
        delivery_id=delivery_id,
    )


# --- File Transfer & Background Processing APIs ---


@router.post(
    "/{delivery_id}/transfer",
    response_model=TransferJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start delivery file transfer",
)
def start_file_transfer(
    delivery_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Start the background file transfer job for a delivery with SHA-256 checksum verification."""
    job = transfer_service.start_transfer(db=db, delivery_id=delivery_id)
    background_tasks.add_task(transfer_service.process_transfer_job, job.id)
    return job


@router.get(
    "/{delivery_id}/transfer-status",
    response_model=TransferJobResponse,
    summary="Get transfer progress and status",
)
def get_transfer_status(
    delivery_id: UUID,
    db: Session = Depends(get_db),
):
    """Retrieve transfer progress, percentages, and individual file outcomes."""
    return transfer_service.get_transfer_status(
        db=db,
        delivery_id=delivery_id,
    )


@router.post(
    "/{delivery_id}/retry-transfer",
    response_model=TransferJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Retry failed file transfers",
)
def retry_file_transfer(
    delivery_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Idempotently retry failed file transfers without duplicate fulfillment of completed files."""
    job = transfer_service.retry_transfer(db=db, delivery_id=delivery_id)
    background_tasks.add_task(transfer_service.process_transfer_job, job.id)
    return job


# --- Delivery Comparison APIs ---


@router.get(
    "/{delivery_id}/compare/{target_delivery_id}",
    response_model=DeliveryComparisonResponse,
    summary="Compare two deliveries",
)
def compare_deliveries(
    delivery_id: UUID,
    target_delivery_id: UUID,
    db: Session = Depends(get_db),
):
    """Compare recordings between two deliveries to detect added, removed, changed, and unchanged recordings."""
    return comparison_service.compare_deliveries(
        db=db,
        base_delivery_id=delivery_id,
        target_delivery_id=target_delivery_id,
    )
