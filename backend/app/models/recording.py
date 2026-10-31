import enum
import uuid
from typing import Any, Dict, Optional, TYPE_CHECKING
from sqlalchemy import BigInteger, Enum as SQLEnum, Float, ForeignKey, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.delivery import Delivery


class QualityStatus(str, enum.Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    PASSED = "PASSED"
    WARNING = "WARNING"
    FAILED = "FAILED"


class Recording(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Recording entity representing a single dataset recording/file within a delivery."""

    __tablename__ = "recordings"

    delivery_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("deliveries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recording_id: Mapped[str] = mapped_column(
        String(150),
        index=True,
        nullable=False,
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    checksum_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    quality_status: Mapped[QualityStatus] = mapped_column(
        SQLEnum(QualityStatus, name="quality_status"),
        default=QualityStatus.PENDING_REVIEW,
        nullable=False,
        index=True,
    )
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    delivery: Mapped["Delivery"] = relationship(
        "Delivery",
        back_populates="recordings",
    )

    def __repr__(self) -> str:
        return f"<Recording id={self.recording_id} file={self.file_name} status={self.quality_status}>"
