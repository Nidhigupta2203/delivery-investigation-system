from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.models.recording import QualityStatus


class RecordingDetailResponse(BaseModel):
    """Detailed recording information, metadata, and quality status."""

    id: UUID
    delivery_id: UUID
    recording_id: str
    file_name: str
    file_path: str
    file_size_bytes: int
    checksum_sha256: Optional[str] = None
    duration_seconds: Optional[float] = None
    quality_status: QualityStatus
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SensorTimeSeriesPoint(BaseModel):
    """Single timestamped observation in sensor time-series telemetry."""

    timestamp: float = Field(..., description="Timestamp in seconds relative to recording start")
    accel_x: float = Field(..., description="Acceleration X axis in m/s^2")
    accel_y: float = Field(..., description="Acceleration Y axis in m/s^2")
    accel_z: float = Field(..., description="Acceleration Z axis in m/s^2 (includes gravity ~9.81)")
    gyro_yaw: float = Field(..., description="Angular velocity yaw in rad/s")
    gyro_pitch: float = Field(..., description="Angular velocity pitch in rad/s")
    gyro_roll: float = Field(..., description="Angular velocity roll in rad/s")
    speed_mps: float = Field(..., description="Chassis speed in meters per second")
    anomaly_flag: bool = Field(default=False, description="Flag indicating anomaly at this timestamp")
    anomaly_type: Optional[str] = Field(default=None, description="Type of anomaly if detected")


class SensorTimeSeriesResponse(BaseModel):
    """Full time-series sensor response for recording playback analysis."""

    recording_id: str
    duration_seconds: float
    sampling_rate_hz: float
    data_points: List[SensorTimeSeriesPoint]
    anomalies_detected: int


class AnomalyEvidence(BaseModel):
    """Specific anomaly observation logged by an investigator."""

    timestamp: Optional[float] = None
    category: str = Field(..., description="Category, e.g. SENSOR_DRIFT, FRAME_DROP, TIMING_JITTER")
    description: str
    severity: str = Field(default="WARNING", description="INFO, WARNING, or CRITICAL")


class RecordingInvestigationUpdate(BaseModel):
    """Schema for updating quality review decisions and attaching investigation evidence."""

    quality_status: QualityStatus = Field(..., description="Updated quality assessment")
    reviewer_notes: Optional[str] = Field(None, max_length=2000, description="Detailed reviewer notes")
    reviewer_name: Optional[str] = Field(None, max_length=150, description="Reviewer or QA engineer identifier")
    anomalies: Optional[List[AnomalyEvidence]] = Field(default=None, description="List of observed anomalies")
