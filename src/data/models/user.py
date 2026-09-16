from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import TIMESTAMP, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.data.models.video import Video


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(
        String(), nullable=False, unique=True, index=True
    )
    full_name: Mapped[str] = mapped_column(String(), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(), nullable=False)
    videos: Mapped[list["Video"]] = relationship(back_populates="author")

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )
