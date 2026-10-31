import enum
import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import BigInteger, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.delivery import Delivery
    from app.models.recording import Recording


class TransferJobStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class FileTransferStatus(str, enum.Enum):
    PENDING = "PENDING"
    TRANSFERRING = "TRANSFERRING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class TransferJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Tracks overall execution, progress, and retries of a delivery file transfer."""

    __tablename__ = "transfer_jobs"

    delivery_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("deliveries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[TransferJobStatus] = mapped_column(
        SQLEnum(TransferJobStatus, name="transfer_job_status"),
        default=TransferJobStatus.PENDING,
        nullable=False,
        index=True,
    )
    total_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    transferred_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    transferred_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    delivery: Mapped["Delivery"] = relationship("Delivery")
    file_transfers: Mapped[List["FileTransfer"]] = relationship(
        "FileTransfer",
        back_populates="transfer_job",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<TransferJob id={self.id} status={self.status} progress={self.transferred_files}/{self.total_files}>"


class FileTransfer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Tracks individual file transfer outcomes, checksums, and retry states."""

    __tablename__ = "file_transfers"

    transfer_job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("transfer_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recording_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("recordings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    source_key: Mapped[str] = mapped_column(String(500), nullable=False)
    target_bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    target_key: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    expected_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    actual_checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[FileTransferStatus] = mapped_column(
        SQLEnum(FileTransferStatus, name="file_transfer_status"),
        default=FileTransferStatus.PENDING,
        nullable=False,
        index=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    transferred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    transfer_job: Mapped["TransferJob"] = relationship(
        "TransferJob",
        back_populates="file_transfers",
    )
    recording: Mapped["Recording"] = relationship("Recording")

    def __repr__(self) -> str:
        return f"<FileTransfer key={self.source_key} status={self.status}>"
