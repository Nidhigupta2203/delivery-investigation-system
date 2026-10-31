from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.delivery import Delivery, DeliveryStatus
from app.models.recording import QualityStatus, Recording
from app.schemas.manifest import (
    ManifestCreate,
    ManifestRecordingResponse,
    ManifestResponse,
)


def register_manifest(
    db: Session,
    delivery_id: UUID,
    data: ManifestCreate,
) -> ManifestResponse:
    """Register or replace recording items in a delivery manifest."""
    delivery = db.get(Delivery, delivery_id)
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery with ID '{delivery_id}' not found.",
        )

    if delivery.status not in (DeliveryStatus.PLANNED, DeliveryStatus.REJECTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Manifest can only be registered for PLANNED or REJECTED deliveries (current status: {delivery.status.value}).",
        )

    if data.source_location:
        delivery.source_location = data.source_location
    if data.target_location:
        delivery.target_location = data.target_location

    # Remove previous recordings for this delivery if updating a PLANNED manifest
    existing_recordings = db.scalars(
        select(Recording).where(Recording.delivery_id == delivery.id)
    ).all()
    for rec in existing_recordings:
        db.delete(rec)

    # Register each recording from the manifest
    created_recordings = []
    total_bytes = 0

    for item in data.recordings:
        recording = Recording(
            delivery_id=delivery.id,
            recording_id=item.recording_id,
            file_name=item.file_name,
            file_path=item.file_path or item.source_key or item.file_name,
            file_size_bytes=item.file_size_bytes,
            checksum_sha256=item.checksum_sha256,
            duration_seconds=item.duration_seconds,
            quality_status=QualityStatus.PENDING_REVIEW,
            metadata_json=item.metadata_json,
        )
        db.add(recording)
        created_recordings.append(recording)
        total_bytes += item.file_size_bytes

    db.commit()

    for r in created_recordings:
        db.refresh(r)
    db.refresh(delivery)

    return ManifestResponse(
        delivery_id=delivery.id,
        delivery_number=delivery.delivery_number,
        source_location=delivery.source_location,
        target_location=delivery.target_location,
        total_recordings=len(created_recordings),
        total_bytes=total_bytes,
        recordings=[ManifestRecordingResponse.model_validate(r) for r in created_recordings],
    )


def get_manifest(db: Session, delivery_id: UUID) -> ManifestResponse:
    """Retrieve the manifest and recording metadata for a delivery."""
    delivery = db.get(Delivery, delivery_id)
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery with ID '{delivery_id}' not found.",
        )

    recordings = list(
        db.scalars(
            select(Recording)
            .where(Recording.delivery_id == delivery.id)
            .order_by(Recording.created_at.asc())
        ).all()
    )

    total_bytes = sum(r.file_size_bytes for r in recordings)

    return ManifestResponse(
        delivery_id=delivery.id,
        delivery_number=delivery.delivery_number,
        source_location=delivery.source_location,
        target_location=delivery.target_location,
        total_recordings=len(recordings),
        total_bytes=total_bytes,
        recordings=[ManifestRecordingResponse.model_validate(r) for r in recordings],
    )
