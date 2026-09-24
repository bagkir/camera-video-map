from __future__ import annotations

import uuid

from sqlalchemy import and_, select
from sqlalchemy.orm import joinedload

from src.data.models import Video
from src.data.models.analysis import Analysis, AnalysisStatus, AnalysisType
from src.data.repositories.base_repository import BaseRepository


class AnalysisRepository(BaseRepository[Analysis]):
    def __init__(self, session):
        super().__init__(session, Analysis)

    async def get_by_video(self, video_id) -> list[Analysis]:
        result = await self.session.execute(
            select(self.model).where(self.model.video_id == video_id)
        )
        return list(result.scalars().all())

    async def list_filtered(
        self,
        *,
        video_id=None,
        analysis_type: AnalysisType | None = None,
        status: AnalysisStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Analysis]:
        query = select(self.model)
        conditions = []
        if video_id is not None:
            conditions.append(self.model.video_id == video_id)
        if analysis_type is not None:
            conditions.append(self.model.analysis_type == analysis_type)
        if status is not None:
            conditions.append(self.model.status == status)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_by_camera(
        self,
        *,
        camera_id: uuid.UUID,
        analysis_type: AnalysisType | None = None,
        status: AnalysisStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Analysis]:
        query = (
            select(self.model)
            .join(Video, Video.id == self.model.video_id)
            .options(joinedload(self.model.video))
            .where(Video.camera_id == camera_id)
        )
        conditions = []
        if analysis_type is not None:
            conditions.append(self.model.analysis_type == analysis_type)
        if status is not None:
            conditions.append(self.model.status == status)
        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(self.model.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.unique().scalars().all())
