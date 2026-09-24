import random
import uuid
from datetime import datetime, timezone

from src.core.exceptions import NotFoundException
from src.data.models import Analysis, AnalysisStatus, AnalysisType
from src.data.repositories.analysis_repository import AnalysisRepository
from src.data.repositories.video_repository import VideoRepository


class AnalysisService:
    def __init__(
        self, analysis_repository: AnalysisRepository, video_repository: VideoRepository
    ):
        self.analysis_repository = analysis_repository
        self.video_repository = video_repository

    async def run_mock_analysis(
        self, video_id: uuid.UUID, analysis_type: AnalysisType
    ) -> Analysis:
        """
        ЗАГЛУШКА. Реальный CV-пайплайн не реализован — решение отложено.
        TODO: заменить result на вызов реального алгоритма/внешнего сервиса.
        """
        video = await self.video_repository.get_by_id(video_id)
        if video is None:
            raise NotFoundException("Video", video_id)

        return await self.analysis_repository.create(
            id=uuid.uuid4(),
            video_id=video_id,
            analysis_type=analysis_type,
            status=AnalysisStatus.DONE,
            result=self._mock_result(analysis_type),
            finished_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _mock_result(analysis_type: AnalysisType) -> dict:
        if analysis_type == AnalysisType.TRAFFIC:
            return {"vehicle_count": random.randint(0, 500)}
        return {"avg_speed_kmh": round(random.uniform(10, 120), 1)}

    async def get_by_video(self, video_id: uuid.UUID) -> list[Analysis]:
        video = await self.video_repository.get_by_id(video_id)
        if video is None:
            raise NotFoundException("Video", video_id)
        return await self.analysis_repository.get_by_video(video_id)

    async def list_by_camera(
        self,
        *,
        camera_id: uuid.UUID,
        analysis_type: AnalysisType | None = None,
        status: AnalysisStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Analysis]:
        return await self.analysis_repository.list_by_camera(
            camera_id=camera_id,
            analysis_type=analysis_type,
            status=status,
            limit=limit,
            offset=offset,
        )
