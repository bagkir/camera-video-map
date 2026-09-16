import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.data.models.video import Video


class AnalysisType(str, enum.Enum):
    TRAFFIC = "traffic"
    SPEED = "speed"


class AnalysisStatus(str, enum.Enum):
    DONE = "done"
    RUN = "run"
    ERROR = "error"


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    video_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("videos.id"), index=True)
    video: Mapped["Video"] = relationship(back_populates="analyses")

    analysis_type: Mapped[AnalysisType] = mapped_column(
        SqlEnum(AnalysisType, name="analysis_type")
    )
    status: Mapped[AnalysisStatus] = mapped_column(
        SqlEnum(AnalysisStatus, name="analysis_status"), default=AnalysisStatus.RUN
    )

    result: Mapped[dict | None] = mapped_column(JSON(), comment="Результат обработки")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
