import asyncio
import random
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile

from src.core.config import settings
from src.core.exceptions import AppException
from src.core.minio_client import get_minio_client
from src.data.models.video import TimeOfDay, TracingStatus, Video
from src.data.repositories.video_repository import VideoRepository
from src.domain.services.camera import CameraService
from src.utils.video_probe import extract_first_frame, probe_video

ALLOWED_CONTENT_TYPES = {"video/mp4"}
MAX_UPLOAD_SIZE_BYTES = (
    2 * 1024 * 1024 * 1024
)  # 2 GB — подстроить под реальные требования


class InvalidVideoFileException(AppException):
    def __init__(self, message: str):
        super().__init__(message=message, status_code=422)


class VideoService:
    def __init__(
        self, video_repository: VideoRepository, camera_service: CameraService
    ):
        self.video_repository = video_repository
        self.camera_service = camera_service

    async def upload(
        self, *, file: UploadFile, camera_id: uuid.UUID, author_id: int
    ) -> Video:
        self._validate_declared_type(file)

        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "source.mp4"
            await self._save_to_disk(file, video_path)

            try:
                metadata = await probe_video(str(video_path))
            except ValueError as exc:
                raise InvalidVideoFileException(
                    f"Файл повреждён или не является видео: {exc}"
                ) from exc

            frame_path = Path(tmpdir) / "frame.jpg"
            try:
                await extract_first_frame(str(video_path), str(frame_path))
            except ValueError as exc:
                raise InvalidVideoFileException(
                    f"Не удалось извлечь первый кадр: {exc}"
                ) from exc

            video_id = uuid.uuid4()
            file_key = f"{camera_id}/{video_id}/source.mp4"
            frame_key = f"{camera_id}/{video_id}/frame.jpg"

            await self._put_object(
                video_path, settings.MINIO_BUCKET_VIDEOS, file_key, "video/mp4"
            )
            await self._put_object(
                frame_path, settings.MINIO_BUCKET_FRAMES, frame_key, "image/jpeg"
            )

        video = await self.video_repository.create(
            id=video_id,
            name=f"{file.filename} ({video_id})",
            camera_id=camera_id,
            author_id=author_id,
            duration_seconds=metadata["duration_seconds"],
            resolution_width=metadata["resolution_width"],
            resolution_height=metadata["resolution_height"],
            fps=metadata["fps"],
            time_of_day=random.choice(
                list(TimeOfDay)
            ),  # TODO: заменить на реальное определение (по свету на кадре/метаданным)
            tracing_status=TracingStatus.DONE,
            file_key=file_key,
            first_frame_key=frame_key,
        )

        await self.camera_service.invalidate_geojson_cache()
        return video

    def _validate_declared_type(self, file: UploadFile) -> None:
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise InvalidVideoFileException(
                f"Неподдерживаемый тип файла: {file.content_type}. Ожидается video/mp4"
            )
        if not file.filename or not file.filename.lower().endswith(".mp4"):
            raise InvalidVideoFileException("Файл должен иметь расширение .mp4")

    async def _save_to_disk(self, file: UploadFile, dest: Path) -> None:
        size = 0
        with open(dest, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_SIZE_BYTES:
                    raise InvalidVideoFileException("Файл превышает допустимый размер")
                f.write(chunk)
        if size == 0:
            raise InvalidVideoFileException("Файл пуст")

    async def _put_object(
        self, path: Path, bucket: str, key: str, content_type: str
    ) -> None:
        client = get_minio_client()
        await asyncio.to_thread(
            client.fput_object, bucket, key, str(path), content_type=content_type
        )

    async def get_last_by_author(self, author_id: int, limit: int = 5) -> list[Video]:
        return await self.video_repository.get_last_by_author(
            author_id=author_id, limit=limit
        )

    async def list_filtered(
        self,
        *,
        camera_id=None,
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
        return await self.video_repository.list_filtered(
            camera_id=camera_id,
            author_id=author_id,
            name_search=name_search,
            author_search=author_search,
            uploaded_from=uploaded_from,
            uploaded_to=uploaded_to,
            duration_from=duration_from,
            duration_to=duration_to,
            time_of_day=time_of_day,
            tracing_status=tracing_status,
            limit=limit,
            offset=offset,
        )
