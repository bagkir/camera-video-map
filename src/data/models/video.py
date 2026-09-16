import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.data.models.analysis import Analysis
    from src.data.models.camera import Camera
    from src.data.models.user import User


class TimeOfDay(str, enum.Enum):
    MORNING = "morning"
    DAY = "day"
    EVENING = "evening"
    NIGHT = "night"


class TracingStatus(str, enum.Enum):
    DONE = "done"  # готово
    RUN = "run"  # в процессе
    ERROR = "error"  # ошибка


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(), comment="Наименование видео (содержит id видео)"
    )

    camera_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("d_camera.id"), index=True)
    camera: Mapped["Camera"] = relationship(back_populates="videos")

    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    author: Mapped["User"] = relationship(back_populates="videos")

    duration_seconds: Mapped[int | None] = mapped_column(
        Integer(), comment="Длительность видео, сек"
    )
    resolution_width: Mapped[int | None] = mapped_column(Integer())
    resolution_height: Mapped[int | None] = mapped_column(Integer())
    fps: Mapped[int | None] = mapped_column(Integer())
    time_of_day: Mapped[TimeOfDay | None] = mapped_column(
        SqlEnum(TimeOfDay, name="time_of_day")
    )
    tracing_status: Mapped[TracingStatus] = mapped_column(
        SqlEnum(TracingStatus, name="tracing_status"), default=TracingStatus.RUN
    )

    file_key: Mapped[str] = mapped_column(String(), comment="Ключ видеофайла в MinIO")
    first_frame_key: Mapped[str | None] = mapped_column(
        String(), comment="Ключ первого кадра в MinIO"
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    analyses: Mapped[list["Analysis"]] = relationship(back_populates="video")

    @property
    def counter(self) -> int:
        """Сколько раз обрабатывалось видео — сумма анализов по траффику и скоростям."""
        return len(self.analyses)
