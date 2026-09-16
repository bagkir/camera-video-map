"""
Тесты CameraService.get_geojson: формат GeoJSON, признак has_video (ТЗ 1.2.1
и 1.2.2), поведение кэша в Redis.
"""

import json

from src.data.repositories.camera_repository import CameraRepository
from src.domain.services.camera import CAMERA_GEOJSON_CACHE_KEY, CameraService


async def test_get_geojson_reports_has_video_flag(
    db_session, fake_redis, make_camera, make_user, make_video
):
    await make_camera(camera_name="Без видео")
    camera_with_video = await make_camera(camera_name="С видео")
    author = await make_user()
    await make_video(camera_id=camera_with_video.id, author_id=author.id)

    service = CameraService(CameraRepository(db_session), fake_redis, cache_ttl=300)
    geojson = await service.get_geojson()

    features = {f["properties"]["camera_name"]: f for f in geojson["features"]}
    assert features["Без видео"]["properties"]["has_video"] is False
    assert features["С видео"]["properties"]["has_video"] is True
    assert features["С видео"]["geometry"]["type"] == "Point"
    assert features["С видео"]["geometry"]["coordinates"] == [
        camera_with_video.camera_longitude,
        camera_with_video.camera_latitude,
    ]


async def test_get_geojson_populates_cache(db_session, fake_redis, make_camera):
    await make_camera()
    service = CameraService(CameraRepository(db_session), fake_redis, cache_ttl=300)

    assert await fake_redis.get(CAMERA_GEOJSON_CACHE_KEY) is None
    await service.get_geojson()
    assert await fake_redis.get(CAMERA_GEOJSON_CACHE_KEY) is not None


async def test_get_geojson_uses_cache_without_hitting_db(db_session, fake_redis):
    cached_payload = {"type": "FeatureCollection", "features": ["from-cache"]}
    await fake_redis.set(CAMERA_GEOJSON_CACHE_KEY, json.dumps(cached_payload))

    service = CameraService(CameraRepository(db_session), fake_redis, cache_ttl=300)
    result = await service.get_geojson()

    assert result == cached_payload


async def test_invalidate_geojson_cache(db_session, fake_redis):
    await fake_redis.set(CAMERA_GEOJSON_CACHE_KEY, "{}")
    service = CameraService(CameraRepository(db_session), fake_redis, cache_ttl=300)

    await service.invalidate_geojson_cache()

    assert await fake_redis.get(CAMERA_GEOJSON_CACHE_KEY) is None
