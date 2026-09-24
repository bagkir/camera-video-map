from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.core.exceptions import UnauthorizedException
from src.core.redis_client import get_redis_client
from src.data.models import User
from src.data.repositories import (
    AnalysisRepository,
    CameraRepository,
    UserRepository,
    VideoRepository,
)
from src.domain.services.analysis import AnalysisService
from src.domain.services.auth import AuthService
from src.domain.services.camera import CameraService
from src.domain.services.user_sevice import UserService
from src.domain.services.video import VideoService

# ========== INFRA ==========

DbSessionDep = Annotated[AsyncSession, Depends(get_db)]
RedisDep = Annotated[Redis, Depends(get_redis_client)]


# ========== REPOSITORIES ==========


async def get_analysis_repository(db: DbSessionDep) -> AnalysisRepository:
    return AnalysisRepository(db)


async def get_video_repository(db: DbSessionDep) -> VideoRepository:
    return VideoRepository(db)


async def get_user_repository(db: DbSessionDep) -> UserRepository:
    return UserRepository(db)


async def get_camera_repository(db: DbSessionDep) -> CameraRepository:
    return CameraRepository(db)


AnalysisRepositoryDep = Annotated[AnalysisRepository, Depends(get_analysis_repository)]
VideoRepositoryDep = Annotated[VideoRepository, Depends(get_video_repository)]
UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]
CameraRepositoryDep = Annotated[CameraRepository, Depends(get_camera_repository)]


# ========== SERVICES ==========


def get_auth_service(user_repository: UserRepositoryDep) -> AuthService:
    return AuthService(user_repository=user_repository)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def get_current_user(request: Request, auth_service: AuthServiceDep) -> User:
    token = request.cookies.get("user_access_token")
    if not token:
        raise UnauthorizedException("Not authenticated")
    return await auth_service.get_user_from_access(token)


async def get_camera_service(
    camera_repository: CameraRepositoryDep,
    redis_client: RedisDep,
) -> CameraService:
    return CameraService(
        camera_repository=camera_repository,
        # redis.asyncio.Redis реально удовлетворяет CameraService.RedisLike
        # (get/set/delete есть и они async) — mypy не может это проверить
        # структурно из-за @overload в стабах redis-py под общий sync/async API.
        redis_client=redis_client,  # type: ignore[arg-type]
        cache_ttl=settings.CAMERA_GEOJSON_CACHE_TTL,
    )


CameraServiceDep = Annotated[CameraService, Depends(get_camera_service)]


async def get_analysis_service(
    analysis_repository: AnalysisRepositoryDep,
    video_repository: VideoRepositoryDep,
) -> AnalysisService:
    return AnalysisService(
        analysis_repository=analysis_repository, video_repository=video_repository
    )


async def get_user_service(user_repository: UserRepositoryDep) -> UserService:
    return UserService(user_repository=user_repository)


async def get_video_service(
    video_repository: VideoRepositoryDep,
    camera_service: CameraServiceDep,
) -> VideoService:
    return VideoService(
        video_repository=video_repository, camera_service=camera_service
    )


# ========== PUBLIC DEPS ==========

CurrentUserDep = Annotated[User, Depends(get_current_user)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
AnalysisServiceDep = Annotated[AnalysisService, Depends(get_analysis_service)]
VideoServiceDep = Annotated[VideoService, Depends(get_video_service)]
