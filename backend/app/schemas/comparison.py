import enum
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.models.delivery import DeliveryStatus
from app.models.recording import QualityStatus


class ComparisonDiffType(str, enum.Enum):
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    CHANGED = "CHANGED"
    UNCHANGED = "UNCHANGED"


class ComparisonRecordingDetail(BaseModel):
    """Snapshot of a recording's attributes for comparison."""

    id: UUID
    recording_id: str
    file_name: str
    file_path: str
    file_size_bytes: int
    checksum_sha256: Optional[str] = None
    duration_seconds: Optional[float] = None
    quality_status: QualityStatus
    metadata_json: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class DeliverySummary(BaseModel):
    """Brief metadata of a delivery in a comparison."""

    id: UUID
    order_id: UUID
    delivery_number: str
    status: DeliveryStatus
    total_recordings: int
    total_bytes: int

    model_config = ConfigDict(from_attributes=True)


class ComparisonSummary(BaseModel):
    """Aggregated difference metrics between two deliveries."""

    total_base_recordings: int
    total_target_recordings: int
    added_count: int
    removed_count: int
    changed_count: int
    unchanged_count: int
    checksum_mismatches_count: int
    quality_status_changes_count: int
    size_delta_bytes: int


class DeliveryComparisonItem(BaseModel):
    """Detailed comparison outcome for a specific recording."""

    recording_id: str
    file_name: str
    diff_type: ComparisonDiffType
    diff_reasons: List[str] = Field(default_factory=list)
    base_recording: Optional[ComparisonRecordingDetail] = None
    target_recording: Optional[ComparisonRecordingDetail] = None


class DeliveryComparisonResponse(BaseModel):
    """Full delivery comparison outcome."""

    base_delivery: DeliverySummary
    target_delivery: DeliverySummary
    summary: ComparisonSummary
    items: List[DeliveryComparisonItem]
