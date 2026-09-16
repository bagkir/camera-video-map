import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.data.models.analysis import AnalysisStatus, AnalysisType


class AnalysisRunRequest(BaseModel):
    analysis_type: AnalysisType


class AnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    video_id: uuid.UUID
    analysis_type: AnalysisType
    status: AnalysisStatus
    result: dict | None
    created_at: datetime
    finished_at: datetime | None


class AnalysisListItem(BaseModel):
    id: uuid.UUID
    video_id: uuid.UUID
    video_name: str
    analysis_type: AnalysisType
    status: AnalysisStatus
    result: dict | None
    created_at: datetime
    finished_at: datetime | None
