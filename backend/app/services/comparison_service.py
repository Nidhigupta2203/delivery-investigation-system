from typing import Dict, List, Tuple
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.delivery import Delivery
from app.models.recording import Recording
from app.schemas.comparison import (
    ComparisonDiffType,
    ComparisonRecordingDetail,
    ComparisonSummary,
    DeliveryComparisonItem,
    DeliveryComparisonResponse,
    DeliverySummary,
)


def compare_deliveries(
    db: Session,
    base_delivery_id: UUID,
    target_delivery_id: UUID,
) -> DeliveryComparisonResponse:
    """Compare two deliveries and analyze added, removed, changed, and unchanged recordings."""
    base_delivery = db.get(Delivery, base_delivery_id)
    if not base_delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Base delivery with ID '{base_delivery_id}' not found.",
        )

    target_delivery = db.get(Delivery, target_delivery_id)
    if not target_delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target delivery with ID '{target_delivery_id}' not found.",
        )

    base_recordings: List[Recording] = list(
        db.scalars(
            select(Recording)
            .where(Recording.delivery_id == base_delivery_id)
            .order_by(Recording.recording_id)
        ).all()
    )

    target_recordings: List[Recording] = list(
        db.scalars(
            select(Recording)
            .where(Recording.delivery_id == target_delivery_id)
            .order_by(Recording.recording_id)
        ).all()
    )

    base_map: Dict[Tuple[str, str], Recording] = {
        (rec.recording_id, rec.file_name): rec for rec in base_recordings
    }
    target_map: Dict[Tuple[str, str], Recording] = {
        (rec.recording_id, rec.file_name): rec for rec in target_recordings
    }

    all_keys = list(dict.fromkeys(list(base_map.keys()) + list(target_map.keys())))
    all_keys.sort()

    items: List[DeliveryComparisonItem] = []
    added_count = 0
    removed_count = 0
    changed_count = 0
    unchanged_count = 0
    checksum_mismatches_count = 0
    quality_status_changes_count = 0

    for rec_id, file_name in all_keys:
        in_base = (rec_id, file_name) in base_map
        in_target = (rec_id, file_name) in target_map

        if not in_base and in_target:
            t_rec = target_map[(rec_id, file_name)]
            added_count += 1
            items.append(
                DeliveryComparisonItem(
                    recording_id=rec_id,
                    file_name=file_name,
                    diff_type=ComparisonDiffType.ADDED,
                    diff_reasons=["New recording added in target delivery"],
                    base_recording=None,
                    target_recording=ComparisonRecordingDetail.model_validate(t_rec),
                )
            )
        elif in_base and not in_target:
            b_rec = base_map[(rec_id, file_name)]
            removed_count += 1
            items.append(
                DeliveryComparisonItem(
                    recording_id=rec_id,
                    file_name=file_name,
                    diff_type=ComparisonDiffType.REMOVED,
                    diff_reasons=["Recording removed from target delivery"],
                    base_recording=ComparisonRecordingDetail.model_validate(b_rec),
                    target_recording=None,
                )
            )
        else:
            b_rec = base_map[(rec_id, file_name)]
            t_rec = target_map[(rec_id, file_name)]
            diff_reasons: List[str] = []

            # Check checksum
            if b_rec.checksum_sha256 != t_rec.checksum_sha256:
                diff_reasons.append("Checksum SHA-256 differs (content modified)")
                checksum_mismatches_count += 1

            # Check quality status
            if b_rec.quality_status != t_rec.quality_status:
                diff_reasons.append(
                    f"Quality status changed from {b_rec.quality_status.value} to {t_rec.quality_status.value}"
                )
                quality_status_changes_count += 1

            # Check file size
            if b_rec.file_size_bytes != t_rec.file_size_bytes:
                diff_reasons.append(
                    f"File size changed from {b_rec.file_size_bytes} to {t_rec.file_size_bytes} bytes"
                )

            # Check duration
            if b_rec.duration_seconds != t_rec.duration_seconds:
                diff_reasons.append(
                    f"Duration changed from {b_rec.duration_seconds}s to {t_rec.duration_seconds}s"
                )

            # Check metadata
            if b_rec.metadata_json != t_rec.metadata_json:
                diff_reasons.append("Recording metadata was updated")

            if diff_reasons:
                changed_count += 1
                items.append(
                    DeliveryComparisonItem(
                        recording_id=rec_id,
                        file_name=file_name,
                        diff_type=ComparisonDiffType.CHANGED,
                        diff_reasons=diff_reasons,
                        base_recording=ComparisonRecordingDetail.model_validate(b_rec),
                        target_recording=ComparisonRecordingDetail.model_validate(t_rec),
                    )
                )
            else:
                unchanged_count += 1
                items.append(
                    DeliveryComparisonItem(
                        recording_id=rec_id,
                        file_name=file_name,
                        diff_type=ComparisonDiffType.UNCHANGED,
                        diff_reasons=[],
                        base_recording=ComparisonRecordingDetail.model_validate(b_rec),
                        target_recording=ComparisonRecordingDetail.model_validate(t_rec),
                    )
                )

    base_total_bytes = sum(r.file_size_bytes for r in base_recordings)
    target_total_bytes = sum(r.file_size_bytes for r in target_recordings)

    base_summary = DeliverySummary(
        id=base_delivery.id,
        order_id=base_delivery.order_id,
        delivery_number=base_delivery.delivery_number,
        status=base_delivery.status,
        total_recordings=len(base_recordings),
        total_bytes=base_total_bytes,
    )

    target_summary = DeliverySummary(
        id=target_delivery.id,
        order_id=target_delivery.order_id,
        delivery_number=target_delivery.delivery_number,
        status=target_delivery.status,
        total_recordings=len(target_recordings),
        total_bytes=target_total_bytes,
    )

    summary = ComparisonSummary(
        total_base_recordings=len(base_recordings),
        total_target_recordings=len(target_recordings),
        added_count=added_count,
        removed_count=removed_count,
        changed_count=changed_count,
        unchanged_count=unchanged_count,
        checksum_mismatches_count=checksum_mismatches_count,
        quality_status_changes_count=quality_status_changes_count,
        size_delta_bytes=target_total_bytes - base_total_bytes,
    )

    return DeliveryComparisonResponse(
        base_delivery=base_summary,
        target_delivery=target_summary,
        summary=summary,
        items=items,
    )
