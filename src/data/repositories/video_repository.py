from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.data.models.user import User
from src.data.models.video import TimeOfDay, TracingStatus, Video
from src.data.repositories.base_repository import BaseRepository


class VideoRepository(BaseRepository[Video]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Video)

    async def list_filtered(
        self,
        *,
        camera_id: uuid.UUID | None = None,
        author_id: int | None = None,
        name_search: str | None = None,
        author_search: str | None = None,
        uploaded_from: datetime | None = None,
        uploaded_to: datetime | None = None,
        duration_from: int | None = None,
        duration_to: int | None = None,
        time_of_day: TimeOfDay | None = None,
        tracing_status: TracingStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Video]:
        """
        Фильтры видео из ТЗ 2.3.5 (дата загрузки, продолжительность, время суток,
        обработка трасс, загрузивший) + поиск по названию/автору для Личного
        кабинета — без ролей, искать можно по любому пользователю.
        """
        query = select(self.model).options(
            joinedload(self.model.camera),
            joinedload(self.model.author),
            selectinload(self.model.analyses),
        )
        conditions = []

        if camera_id is not None:
            conditions.append(self.model.camera_id == camera_id)
        if author_id is not None:
            conditions.append(self.model.author_id == author_id)
        if name_search:
            conditions.append(self.model.name.ilike(f"%{name_search}%"))
        if author_search:
            # EXISTS-подзапрос вместо явного join — не конфликтует с joinedload(author)
            conditions.append(
                self.model.author.has(User.full_name.ilike(f"%{author_search}%"))
            )
        if uploaded_from is not None:
            conditions.append(self.model.uploaded_at >= uploaded_from)
        if uploaded_to is not None:
            conditions.append(self.model.uploaded_at <= uploaded_to)
        if duration_from is not None:
            conditions.append(self.model.duration_seconds >= duration_from)
        if duration_to is not None:
            conditions.append(self.model.duration_seconds <= duration_to)
        if time_of_day is not None:
            conditions.append(self.model.time_of_day == time_of_day)
        if tracing_status is not None:
            conditions.append(self.model.tracing_status == tracing_status)

        if conditions:
            query = query.where(and_(*conditions))

        query = (
            query.order_by(self.model.uploaded_at.desc()).offset(offset).limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.unique().scalars().all())

    async def get_last_by_author(self, author_id: int, limit: int = 5) -> list[Video]:
        """Последние загруженные видео — для блока в Личном кабинете."""
        return await self.list_filtered(author_id=author_id, limit=limit)
