from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.storage import storage_service
from app.models.delivery import Delivery, DeliveryStatus
from app.models.recording import QualityStatus, Recording
from app.models.transfer import FileTransfer, FileTransferStatus, TransferJob, TransferJobStatus


def _parse_bucket_and_key(location: str | None, default_bucket: str) -> str:
    """Helper to extract bucket from location string or return default."""
    if not location:
        return default_bucket
    if location.startswith("s3://"):
        parts = location[5:].split("/", 1)
        return parts[0] if parts[0] else default_bucket
    return default_bucket


def start_transfer(db: Session, delivery_id: UUID) -> TransferJob:
    """Initialize a file transfer job and queue recordings for processing."""
    delivery = db.get(Delivery, delivery_id)
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery with ID '{delivery_id}' not found.",
        )

    # Verify delivery has recordings in its manifest
    recordings = list(
        db.scalars(select(Recording).where(Recording.delivery_id == delivery.id)).all()
    )
    if not recordings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot start transfer: Delivery has no recordings in its manifest.",
        )

    # Verify no active transfer is currently running
    active_job = db.scalar(
        select(TransferJob).where(
            TransferJob.delivery_id == delivery.id,
            TransferJob.status.in_([TransferJobStatus.PENDING, TransferJobStatus.IN_PROGRESS]),
        )
    )
    if active_job:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A transfer job is already currently running or pending for this delivery.",
        )

    source_bucket = _parse_bucket_and_key(delivery.source_location, settings.S3_SOURCE_BUCKET)
    target_bucket = _parse_bucket_and_key(delivery.target_location, settings.S3_CUSTOMER_BUCKET)

    total_bytes = sum(r.file_size_bytes for r in recordings)

    # Create master transfer job
    job = TransferJob(
        delivery_id=delivery.id,
        status=TransferJobStatus.PENDING,
        total_files=len(recordings),
        transferred_files=0,
        total_bytes=total_bytes,
        transferred_bytes=0,
        retry_count=0,
    )
    db.add(job)
    db.flush()

    # Create individual file transfer items
    for recording in recordings:
        file_transfer = FileTransfer(
            transfer_job_id=job.id,
            recording_id=recording.id,
            source_bucket=source_bucket,
            source_key=recording.file_path.lstrip('/'),
            target_bucket=target_bucket,
            target_key=f"deliveries/{delivery.delivery_number}/{recording.file_name}",
            file_size_bytes=recording.file_size_bytes,
            expected_checksum=recording.checksum_sha256 or "",
            status=FileTransferStatus.PENDING,
        )
        db.add(file_transfer)

    delivery.status = DeliveryStatus.TRANSFERRING
    db.commit()
    db.refresh(job)

    return get_transfer_status(db, delivery.id)


def get_transfer_status(db: Session, delivery_id: UUID) -> TransferJob:
    """Retrieve the latest transfer job and its individual file transfer statuses."""
    job = db.scalar(
        select(TransferJob)
        .where(TransferJob.delivery_id == delivery_id)
        .options(selectinload(TransferJob.file_transfers))
        .order_by(TransferJob.created_at.desc())
    )
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No transfer job found for delivery '{delivery_id}'.",
        )
    return job


def retry_transfer(db: Session, delivery_id: UUID) -> TransferJob:
    """Idempotently retry failed file transfers without re-transferring completed files."""
    delivery = db.get(Delivery, delivery_id)
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery with ID '{delivery_id}' not found.",
        )

    job = db.scalar(
        select(TransferJob)
        .where(TransferJob.delivery_id == delivery_id)
        .options(selectinload(TransferJob.file_transfers))
        .order_by(TransferJob.created_at.desc())
    )
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No previous transfer job found for delivery '{delivery_id}'.",
        )

    if job.status in (TransferJobStatus.PENDING, TransferJobStatus.IN_PROGRESS):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Transfer job is currently running and cannot be retried yet.",
        )

    if job.status == TransferJobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transfer job is already fully completed.",
        )

    # Re-queue only failed items; preserve already completed files
    for ft in job.file_transfers:
        if ft.status == FileTransferStatus.FAILED:
            ft.status = FileTransferStatus.PENDING
            ft.error_message = None

    job.status = TransferJobStatus.PENDING
    job.retry_count += 1
    job.error_message = None
    delivery.status = DeliveryStatus.TRANSFERRING

    db.commit()
    db.refresh(job)
    return job


def process_transfer_job(job_id: UUID, db: Session = None) -> Optional[TransferJob]:
    """Execute the file transfer job: stream files, verify SHA-256 checksums,

    and update progress in the database.
    """
    should_close_db = False
    if db is None:
        db = SessionLocal()
        should_close_db = True

    try:
        job = db.scalar(
            select(TransferJob)
            .where(TransferJob.id == job_id)
            .options(selectinload(TransferJob.file_transfers))
        )
        if not job:
            return None

        # Mark job as in-progress
        job.status = TransferJobStatus.IN_PROGRESS
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        storage_service.ensure_default_buckets()

        for ft in job.file_transfers:
            # Idempotency / Safe retry: skip files that already succeeded
            if ft.status == FileTransferStatus.COMPLETED:
                continue

            ft.status = FileTransferStatus.TRANSFERRING
            db.commit()

            # Execute real S3 transfer with streaming SHA-256 checksum verification
            success, actual_checksum, size_bytes, err = storage_service.transfer_and_verify(
                source_bucket=ft.source_bucket,
                source_key=ft.source_key,
                target_bucket=ft.target_bucket,
                target_key=ft.target_key,
                expected_checksum=ft.expected_checksum,
            )

            ft.actual_checksum = actual_checksum
            if success:
                ft.status = FileTransferStatus.COMPLETED
                ft.transferred_at = datetime.now(timezone.utc)
                ft.error_message = None

                # Update associated recording quality status to PASSED
                recording = db.get(Recording, ft.recording_id)
                if recording:
                    recording.quality_status = QualityStatus.PASSED
                    recording.checksum_sha256 = actual_checksum
                    if size_bytes > 0:
                        recording.file_size_bytes = size_bytes
            else:
                ft.status = FileTransferStatus.FAILED
                ft.error_message = err

                # Mark recording quality status to FAILED
                recording = db.get(Recording, ft.recording_id)
                if recording:
                    recording.quality_status = QualityStatus.FAILED

            # Atomically update transferred counts on the master job
            job.transferred_files = sum(
                1 for f in job.file_transfers if f.status == FileTransferStatus.COMPLETED
            )
            job.transferred_bytes = sum(
                f.file_size_bytes for f in job.file_transfers if f.status == FileTransferStatus.COMPLETED
            )
            db.commit()

        # Evaluate final job state
        all_completed = all(f.status == FileTransferStatus.COMPLETED for f in job.file_transfers)
        delivery = db.get(Delivery, job.delivery_id)

        if all_completed:
            job.status = TransferJobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            job.error_message = None
            if delivery:
                delivery.status = DeliveryStatus.TRANSFERRED
        else:
            job.status = TransferJobStatus.FAILED
            failed_count = sum(1 for f in job.file_transfers if f.status == FileTransferStatus.FAILED)
            job.error_message = f"{failed_count} file(s) failed checksum verification or transfer."

        db.commit()
        db.refresh(job)
        return job

    finally:
        if should_close_db:
            db.close()


def poll_and_process_pending_jobs(db: Session = None) -> int:
    """Check for pending transfer jobs and process them."""
    should_close_db = False
    if db is None:
        db = SessionLocal()
        should_close_db = True

    try:
        pending_job_ids = list(
            db.scalars(
                select(TransferJob.id)
                .where(TransferJob.status == TransferJobStatus.PENDING)
                .order_by(TransferJob.created_at.asc())
            ).all()
        )

        for job_id in pending_job_ids:
            process_transfer_job(job_id=job_id, db=db)

        return len(pending_job_ids)
    finally:
        if should_close_db:
            db.close()
