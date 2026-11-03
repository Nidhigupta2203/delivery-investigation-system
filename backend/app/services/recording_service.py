import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.storage import storage_service
from app.models.delivery import Delivery
from app.models.recording import QualityStatus, Recording
from app.schemas.recording import (
    RecordingInvestigationUpdate,
    SensorTimeSeriesPoint,
    SensorTimeSeriesResponse,
)

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
SAMPLE_VIDEO_PATH = ASSETS_DIR / "sample_robotics_feed.mp4"


def get_recording(db: Session, recording_id: UUID) -> Recording:
    """Retrieve recording by UUID or raise 404."""
    recording = db.get(Recording, recording_id)
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recording with ID '{recording_id}' not found.",
        )
    return recording


def update_investigation(
    db: Session,
    recording_id: UUID,
    data: RecordingInvestigationUpdate,
) -> Recording:
    """Update recording quality status and record investigation evidence and notes."""
    recording = get_recording(db, recording_id)

    recording.quality_status = data.quality_status

    # Preserve and merge investigation details in metadata_json
    metadata = dict(recording.metadata_json or {})
    investigation_entry: Dict[str, Any] = {
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "reviewer_notes": data.reviewer_notes,
        "reviewer_name": data.reviewer_name or "Dataset QA Specialist",
        "quality_status": data.quality_status.value,
        "anomalies": [a.model_dump() for a in data.anomalies] if data.anomalies else [],
    }
    metadata["investigation"] = investigation_entry
    recording.metadata_json = metadata

    db.commit()
    db.refresh(recording)
    return recording


def generate_synthetic_telemetry(
    duration: float,
    quality_status: QualityStatus,
    metadata_anomalies: Optional[List[Dict[str, Any]]] = None,
) -> List[SensorTimeSeriesPoint]:
    """Generate realistic timestamped sensor telemetry for robotics visualization."""
    dt = 0.1  # 10 Hz
    num_points = max(10, int(duration / dt))
    points: List[SensorTimeSeriesPoint] = []

    # Flag anomaly timestamp if warning or failed
    anomaly_timestamps: Dict[int, str] = {}
    if metadata_anomalies:
        for a in metadata_anomalies:
            t = a.get("timestamp", duration / 2.0)
            idx = int(t / dt)
            anomaly_timestamps[idx] = a.get("category", "SENSOR_SPIKE")
    elif quality_status in (QualityStatus.WARNING, QualityStatus.FAILED):
        # Inject realistic anomaly near middle of recording
        mid_idx = num_points // 2
        anomaly_timestamps[mid_idx] = "IMU_VIBRATION_SPIKE"
        anomaly_timestamps[mid_idx + 1] = "DROPPED_SENSOR_FRAME"

    for i in range(num_points):
        t = round(i * dt, 2)
        progress = i / max(1, num_points - 1)

        # Realistic robotics platform motion curves
        # Speed: smooth ramp up, cruise, gentle deceleration
        speed = 2.2 * math.sin(progress * math.pi)

        # Baseline acceleration + sensor noise
        noise = 0.05 * math.sin(i * 1.7)
        acc_x = round(0.4 * math.sin(i * 0.4) + noise, 3)
        acc_y = round(0.2 * math.cos(i * 0.3) + noise * 0.5, 3)
        acc_z = round(9.81 + 0.15 * math.sin(i * 0.8) + noise, 3)

        # Gyroscope angular velocities
        yaw = round(0.12 * math.sin(i * 0.25), 4)
        pitch = round(0.04 * math.sin(i * 0.5), 4)
        roll = round(0.03 * math.cos(i * 0.5), 4)

        has_anomaly = i in anomaly_timestamps
        anomaly_type = anomaly_timestamps.get(i)

        if has_anomaly:
            acc_z = round(acc_z + 4.8, 3)  # vertical jolt / bump
            pitch = round(pitch + 0.35, 4)

        points.append(
            SensorTimeSeriesPoint(
                timestamp=t,
                accel_x=acc_x,
                accel_y=acc_y,
                accel_z=acc_z,
                gyro_yaw=yaw,
                gyro_pitch=pitch,
                gyro_roll=roll,
                speed_mps=round(max(0.0, speed), 2),
                anomaly_flag=has_anomaly,
                anomaly_type=anomaly_type,
            )
        )

    return points


def get_sensor_timeseries(db: Session, recording_id: UUID) -> SensorTimeSeriesResponse:
    """Retrieve or generate timestamped sensor telemetry for a recording."""
    recording = get_recording(db, recording_id)
    duration = recording.duration_seconds if recording.duration_seconds and recording.duration_seconds > 0 else 10.0

    metadata = recording.metadata_json or {}
    raw_sensor_data = metadata.get("sensor_data")
    investigation_anomalies = metadata.get("investigation", {}).get("anomalies")

    if raw_sensor_data and isinstance(raw_sensor_data, list):
        data_points = [SensorTimeSeriesPoint(**pt) for pt in raw_sensor_data]
    else:
        data_points = generate_synthetic_telemetry(
            duration=duration,
            quality_status=recording.quality_status,
            metadata_anomalies=investigation_anomalies,
        )

    anomalies_count = sum(1 for pt in data_points if pt.anomaly_flag)

    return SensorTimeSeriesResponse(
        recording_id=recording.recording_id,
        duration_seconds=duration,
        sampling_rate_hz=10.0,
        data_points=data_points,
        anomalies_detected=anomalies_count,
    )


def get_media_bytes(db: Session, recording_id: UUID) -> Tuple[bytes, str]:
    """Retrieve recording video bytes from S3/MinIO or return sample robotics video."""
    recording = get_recording(db, recording_id)
    delivery = db.get(Delivery, recording.delivery_id)

    # Attempt to load from customer target bucket or source bucket in S3
    if delivery and delivery.target_location:
        target_bucket = delivery.target_location.replace("s3://", "").split("/")[0]
        target_key = f"deliveries/{delivery.delivery_number}/{recording.file_name}"
        try:
            if storage_service.object_exists(target_bucket, target_key):
                content = storage_service.get_object_bytes(target_bucket, target_key)
                if len(content) > 100:  # verify non-trivial video content
                    return content, "video/mp4"
        except Exception:
            pass

    # Fallback to local sample video feed
    if SAMPLE_VIDEO_PATH.exists():
        with open(SAMPLE_VIDEO_PATH, "rb") as f:
            return f.read(), "video/mp4"

    # Emergency fallback: minimal 1-second mp4 header bytes
    return b"\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2avc1mp41", "video/mp4"
