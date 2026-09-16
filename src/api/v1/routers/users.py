from fastapi import APIRouter

from src.api.v1.dependencies import CurrentUserDep, UserServiceDep, VideoServiceDep
from src.api.v1.schemas.user import UserDashboard, UserOut
from src.api.v1.schemas.video import VideoListItem

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
async def list_users(_: CurrentUserDep, user_service: UserServiceDep):
    return await user_service.get_all()


@router.get("/me/dashboard", response_model=UserDashboard)
async def get_my_dashboard(
    current_user: CurrentUserDep, video_service: VideoServiceDep
):
    """Личный кабинет (ТЗ): инфа о пользователе + последние загруженные видео."""

    recent_videos = await video_service.get_last_by_author(current_user.id, limit=5)
    return UserDashboard(
        user=UserOut.model_validate(current_user),
        recent_videos=[
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
            for v in recent_videos
        ],
    )
