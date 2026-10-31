from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.models.recording import QualityStatus


class ManifestItemCreate(BaseModel):
    """Schema for an individual recording item within a manifest registration."""

    recording_id: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="Dataset identifier for the recording (e.g. REC-20261031-001)",
    )
    file_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Filename (e.g. front_camera.mp4)",
    )
    file_path: Optional[str] = Field(
        None,
        max_length=500,
        description="Relative file path within storage (defaults to file_name if omitted)",
    )
    source_key: Optional[str] = Field(
        None,
        max_length=500,
        description="Specific source S3 key if different from file_path",
    )
    target_key: Optional[str] = Field(
        None,
        max_length=500,
        description="Specific destination S3 key if different from deliveries/{number}/{file_name}",
    )
    file_size_bytes: int = Field(
        default=0,
        ge=0,
        description="File size in bytes",
    )
    checksum_sha256: str = Field(
        ...,
        min_length=64,
        max_length=64,
        pattern=r"^[a-fA-F0-9]{64}$",
        description="Hex-encoded SHA-256 checksum",
    )
    duration_seconds: Optional[float] = Field(
        None,
        ge=0.0,
        description="Duration of recording in seconds",
    )
    metadata_json: Optional[Dict[str, Any]] = Field(
        None,
        description="Sensor, camera, and environment recording metadata",
    )


class ManifestCreate(BaseModel):
    """Schema for registering a full delivery manifest."""

    manifest_version: str = Field(
        default="1.0",
        description="Manifest format version",
    )
    source_location: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional override for delivery source bucket or URI",
    )
    target_location: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional override for delivery target bucket or URI",
    )
    recordings: List[ManifestItemCreate] = Field(
        ...,
        min_length=1,
        description="List of recording entries in this delivery manifest",
    )


class ManifestRecordingResponse(BaseModel):
    """Schema for serialized recording entry in a manifest."""

    id: UUID
    delivery_id: UUID
    recording_id: str
    file_name: str
    file_path: str
    file_size_bytes: int
    checksum_sha256: Optional[str]
    duration_seconds: Optional[float]
    quality_status: QualityStatus
    metadata_json: Optional[Dict[str, Any]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ManifestResponse(BaseModel):
    """Schema for returning the inspected delivery manifest."""

    delivery_id: UUID
    delivery_number: str
    source_location: Optional[str]
    target_location: Optional[str]
    total_recordings: int
    total_bytes: int
    recordings: List[ManifestRecordingResponse]
