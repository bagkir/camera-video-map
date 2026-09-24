import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.data.models.video import Video


class Camera(Base):
    __tablename__ = "d_camera"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    camera_id: Mapped[str] = mapped_column(
        String(), unique=True, index=True, comment="Номер камеры"
    )
    camera_class_cd: Mapped[int | None] = mapped_column(
        Integer(), comment="Идентификатор класса камеры"
    )
    camera_class: Mapped[str | None] = mapped_column(String(), comment="Класс камеры")
    model: Mapped[str | None] = mapped_column(String(), comment="Модель")
    camera_name: Mapped[str] = mapped_column(
        String(), index=True, comment="Название камеры"
    )
    camera_place: Mapped[str | None] = mapped_column(String(), comment="Адрес")
    camera_place_cd: Mapped[int | None] = mapped_column(
        Integer(), comment="Идентификатор адреса"
    )
    serial_number: Mapped[str | None] = mapped_column(
        String(), comment="Серийный номер"
    )
    camera_type_cd: Mapped[int | None] = mapped_column(
        Integer(), comment="Идентификатор типа камеры"
    )
    camera_type: Mapped[str | None] = mapped_column(String(), comment="Тип камеры")
    camera_latitude: Mapped[float] = mapped_column(Float(), comment="Широта")
    camera_longitude: Mapped[float] = mapped_column(Float(), comment="Долгота")
    archive: Mapped[bool] = mapped_column(
        Boolean(), default=False, comment="Признак архивной записи"
    )
    azimuth: Mapped[int | None] = mapped_column(Integer(), comment="Азимут")
    process_dttm: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    videos: Mapped[list["Video"]] = relationship(back_populates="camera")

    @property
    def has_video(self) -> bool:
        return len(self.videos) > 0
