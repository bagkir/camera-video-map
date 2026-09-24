import uuid
from datetime import datetime

from fastapi import APIRouter, File, Form, Query, UploadFile

from src.api.v1.dependencies import CameraServiceDep, CurrentUserDep, VideoServiceDep
from src.api.v1.schemas.video import VideoListItem, VideoOut
from src.core.exceptions import NotFoundException
from src.data.models import TimeOfDay, TracingStatus

router = APIRouter(prefix="/videos", tags=["videos"])


@router.post("", response_model=VideoOut, status_code=201)
async def upload_video(
    current_user: CurrentUserDep,
    video_service: VideoServiceDep,
    camera_service: CameraServiceDep,
    camera_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
):
    camera = await camera_service.get_by_id(camera_id)
    if camera is None:
        raise NotFoundException("Camera", camera_id)

    return await video_service.upload(
        file=file, camera_id=camera_id, author_id=current_user.id
    )


@router.get("", response_model=list[VideoListItem])
async def list_videos(
    _: CurrentUserDep,
    video_service: VideoServiceDep,
    camera_id: uuid.UUID | None = None,
    author_id: int | None = None,
    name_search: str | None = None,
    author_search: str | None = None,
    uploaded_from: datetime | None = None,
    uploaded_to: datetime | None = None,
    duration_from: int | None = Query(None, ge=0),
    duration_to: int | None = Query(None, ge=0),
    time_of_day: TimeOfDay | None = None,
    tracing_status: TracingStatus | None = None,
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
):
    """
    Общий список видео с фильтрами (ТЗ 2.3.5). Без ролей — виден результат
    обработки видео от всех пользователей, поиск по названию/автору.
    """

    videos = await video_service.list_filtered(
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
    return [
        VideoListItem(
            id=v.id,
            name=v.name,
            camera_id=v.camera_id,
            camera_name=v.camera.camera_name,
            author_id=v.author_id,
            author_name=v.author.full_name,
            duration_seconds=v.duration_seconds,
            resolution_width=v.resolution_width,
            resolution_height=v.resolution_height,
            fps=v.fps,
            time_of_day=v.time_of_day,
            tracing_status=v.tracing_status,
            counter=v.counter,
            uploaded_at=v.uploaded_at,
        )
        for v in videos
    ]
