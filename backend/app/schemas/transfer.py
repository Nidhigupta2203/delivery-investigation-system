from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, computed_field

from app.models.transfer import FileTransferStatus, TransferJobStatus


class FileTransferResponse(BaseModel):
    """Schema for individual file transfer tracking."""

    id: UUID
    recording_id: UUID
    source_bucket: str
    source_key: str
    target_bucket: str
    target_key: str
    file_size_bytes: int
    expected_checksum: str
    actual_checksum: Optional[str]
    status: FileTransferStatus
    error_message: Optional[str]
    transferred_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class TransferJobResponse(BaseModel):
    """Schema for transfer job status, progress, and file outcomes."""

    id: UUID
    delivery_id: UUID
    status: TransferJobStatus
    total_files: int
    transferred_files: int
    total_bytes: int
    transferred_bytes: int
    retry_count: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    file_transfers: List[FileTransferResponse] = []

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    def progress_percentage(self) -> float:
        """Calculate the percentage of files transferred."""
        if self.total_files == 0:
            return 100.0 if self.status == TransferJobStatus.COMPLETED else 0.0
        return round((self.transferred_files / self.total_files) * 100.0, 2)
