import json
import logging
import uuid
from typing import Any, Protocol

from redis.exceptions import RedisError

from src.data.models import Camera
from src.data.repositories.camera_repository import CameraRepository

logger = logging.getLogger(__name__)

CAMERA_GEOJSON_CACHE_KEY = "cameras:geojson"


class RedisLike(Protocol):
    """
    Минимальный интерфейс, который нужен сервису от Redis-клиента — позволяет
    подставлять в тестах простую in-memory замену вместо реального
    redis.asyncio.Redis, не наследуясь от него. Параметры позиционные (`/`),
    чтобы не зависеть от точных имён (`key` vs `name`) в redis-py.

    mypy не умеет чисто сверить это с реальным redis.asyncio.Redis — его
    stub'ы используют @overload под общий sync/async API, и Protocol-проверка
    перегруженных методов у mypy работает не полностью. Поэтому на месте
    реальной инъекции (dependencies.py) стоит точечный type: ignore.
    """

    async def get(self, key: str, /) -> Any: ...
    async def set(self, key: str, value: str, /, *, ex: int | None = None) -> Any: ...
    async def delete(self, key: str, /) -> Any: ...


class CameraService:
    def __init__(
        self,
        camera_repository: CameraRepository,
        redis_client: RedisLike,
        cache_ttl: int,
    ):
        self.camera_repository = camera_repository
        self.redis = redis_client
        self.cache_ttl = cache_ttl

    async def get_geojson(self) -> dict:
        try:
            cached = await self.redis.get(CAMERA_GEOJSON_CACHE_KEY)
            if cached is not None:
                return json.loads(cached)
        except RedisError:
            logger.warning(
                "Redis unavailable on read, falling back to DB", exc_info=True
            )

        geojson = await self._build_geojson()

        try:
            await self.redis.set(
                CAMERA_GEOJSON_CACHE_KEY, json.dumps(geojson), ex=self.cache_ttl
            )
        except RedisError:
            logger.warning("Failed to write geojson cache", exc_info=True)

        return geojson

    async def invalidate_geojson_cache(self) -> None:
        """Вызывать при создании/удалении видео — has_video мог измениться."""
        try:
            await self.redis.delete(CAMERA_GEOJSON_CACHE_KEY)
        except RedisError:
            logger.warning("Failed to invalidate geojson cache", exc_info=True)

    async def _build_geojson(self) -> dict:
        rows = await self.camera_repository.list_all_with_video_count()
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "id": str(camera.id),
                        "camera_id": camera.camera_id,
                        "camera_name": camera.camera_name,
                        "has_video": video_count > 0,
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            camera.camera_longitude,
                            camera.camera_latitude,
                        ],
                    },
                }
                for camera, video_count in rows
            ],
        }

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

        return await self.camera_repository.list_filtered(
            search=search,
            videos_from=videos_from,
            videos_to=videos_to,
            model=model,
            camera_type=camera_type,
            camera_class=camera_class,
            limit=limit,
            offset=offset,
        )

    async def get_by_id(self, id: int | uuid.UUID) -> Camera | None:
        return await self.camera_repository.get_by_id(id=id)

    async def get_by_id_with_count(
        self, camera_id: uuid.UUID
    ) -> tuple[Camera, int] | None:
        return await self.camera_repository.get_by_id_with_video_count(camera_id)
