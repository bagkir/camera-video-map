import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.data.models.video import TimeOfDay, TracingStatus


class VideoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    camera_id: uuid.UUID
    author_id: int
    duration_seconds: int | None
    resolution_width: int | None
    resolution_height: int | None
    fps: int | None
    time_of_day: TimeOfDay | None
    tracing_status: TracingStatus
    uploaded_at: datetime


class VideoListItem(BaseModel):
    id: uuid.UUID
    name: str
    camera_id: uuid.UUID
    camera_name: str
    author_id: int
    author_name: str
    duration_seconds: int | None
    resolution_width: int | None
    resolution_height: int | None
    fps: int | None
    time_of_day: TimeOfDay | None
    tracing_status: TracingStatus
    counter: int
    uploaded_at: datetime
