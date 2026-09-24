from __future__ import annotations

import uuid

from sqlalchemy import ColumnElement, and_, func, select

from src.data.models.camera import Camera
from src.data.models.video import Video
from src.data.repositories.base_repository import BaseRepository


class CameraRepository(BaseRepository[Camera]):
    def __init__(self, session):
        super().__init__(session, Camera)

    async def get_by_camera_id(self, camera_id: str) -> Camera | None:
        result = await self.session.execute(
            select(self.model).where(self.model.camera_id == camera_id)
        )
        return result.scalar_one_or_none()

    async def list_filtered(
        self,
        *,
        search: str | None = None,
        videos_from: int | None = None,
        videos_to: int | None = None,
        model: str | None = None,
        camera_type: str | None = None,
        camera_class: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[tuple[Camera, int]]:
        """
        Фильтры камер из ТЗ 1.3.4: полнотекстовый поиск по названию,
        диапазон кол-ва загруженных видео, модель, тип, класс.
        Возвращает пары (Camera, video_count).
        """
        video_count_subq = (
            select(Video.camera_id, func.count(Video.id).label("video_count"))
            .group_by(Video.camera_id)
            .subquery()
        )
        video_count_col = func.coalesce(video_count_subq.c.video_count, 0)

        query = select(Camera, video_count_col.label("video_count")).outerjoin(
            video_count_subq, video_count_subq.c.camera_id == Camera.id
        )

        conditions: list[ColumnElement[bool]] = []
        if search:
            conditions.append(Camera.camera_name.ilike(f"%{search}%"))
        if model:
            conditions.append(Camera.model == model)
        if camera_type:
            conditions.append(Camera.camera_type == camera_type)
        if camera_class:
            conditions.append(Camera.camera_class == camera_class)
        if videos_from is not None:
            conditions.append(video_count_col >= videos_from)
        if videos_to is not None:
            conditions.append(video_count_col <= videos_to)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return [(row.Camera, row.video_count) for row in result.all()]

    async def list_all_with_video_count(self) -> list[tuple[Camera, int]]:
        """Все камеры с количеством видео — источник для GeoJSON, без пагинации."""
        video_count_subq = (
            select(Video.camera_id, func.count(Video.id).label("video_count"))
            .group_by(Video.camera_id)
            .subquery()
        )
        video_count_col = func.coalesce(video_count_subq.c.video_count, 0)
        query = select(Camera, video_count_col.label("video_count")).outerjoin(
            video_count_subq, video_count_subq.c.camera_id == Camera.id
        )
        result = await self.session.execute(query)
        return [(row.Camera, row.video_count) for row in result.all()]

    async def get_by_id_with_video_count(
        self, camera_id: uuid.UUID
    ) -> tuple[Camera, int] | None:
        video_count_subq = (
            select(Video.camera_id, func.count(Video.id).label("video_count"))
            .group_by(Video.camera_id)
            .subquery()
        )
        video_count_col = func.coalesce(video_count_subq.c.video_count, 0)
        query = (
            select(Camera, video_count_col.label("video_count"))
            .outerjoin(video_count_subq, video_count_subq.c.camera_id == Camera.id)
            .where(Camera.id == camera_id)
        )
        result = await self.session.execute(query)
        row = result.first()
        return (row.Camera, row.video_count) if row else None
