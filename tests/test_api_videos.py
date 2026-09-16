"""
Тесты загрузки и списка видео (ТЗ 1.3.3: валидация типа + чтения файла,
1.3.5: сохранение первого кадра, 2.3.5: фильтры).
"""

import uuid

import pytest

import src.domain.services.video as video_service_module


class _FakeMinioClient:
    """Замена MinIO-клиента: fput_object пишет только в память."""

    def __init__(self) -> None:
        self.uploaded: list[tuple[str, str, str]] = []

    def fput_object(self, bucket: str, key: str, path: str, content_type: str) -> None:
        self.uploaded.append((bucket, key, content_type))


@pytest.fixture(autouse=True)
def fake_minio(monkeypatch: pytest.MonkeyPatch) -> _FakeMinioClient:
    fake = _FakeMinioClient()
    monkeypatch.setattr(video_service_module, "get_minio_client", lambda: fake)
    return fake


async def test_upload_requires_authentication(client, sample_mp4):
    with open(sample_mp4, "rb") as f:
        response = await client.post(
            "/api/v1/videos",
            data={"camera_id": str(uuid.uuid4())},
            files={"file": ("clip.mp4", f, "video/mp4")},
        )
    assert response.status_code == 401


async def test_upload_rejects_unknown_camera(logged_in_client, sample_mp4):
    with open(sample_mp4, "rb") as f:
        response = await logged_in_client.post(
            "/api/v1/videos",
            data={"camera_id": str(uuid.uuid4())},
            files={"file": ("clip.mp4", f, "video/mp4")},
        )
    assert response.status_code == 404


async def test_upload_rejects_wrong_content_type(
    logged_in_client, make_camera, sample_mp4
):
    camera = await make_camera()
    with open(sample_mp4, "rb") as f:
        response = await logged_in_client.post(
            "/api/v1/videos",
            data={"camera_id": str(camera.id)},
            files={"file": ("clip.mp4", f, "text/plain")},
        )
    assert response.status_code == 422


async def test_upload_rejects_non_video_file(logged_in_client, make_camera, broken_mp4):
    camera = await make_camera()
    with open(broken_mp4, "rb") as f:
        response = await logged_in_client.post(
            "/api/v1/videos",
            data={"camera_id": str(camera.id)},
            files={"file": ("broken.mp4", f, "video/mp4")},
        )
    assert response.status_code == 422


async def test_upload_success_stores_video_and_frame(
    logged_in_client, make_camera, sample_mp4, fake_minio
):
    camera = await make_camera()
    with open(sample_mp4, "rb") as f:
        response = await logged_in_client.post(
            "/api/v1/videos",
            data={"camera_id": str(camera.id)},
            files={"file": ("clip.mp4", f, "video/mp4")},
        )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["camera_id"] == str(camera.id)
    assert body["duration_seconds"] == 1
    assert body["resolution_width"] == 320
    assert body["tracing_status"] == "done"

    # видео и первый кадр должны попасть в MinIO в разные бакеты
    buckets = {upload[0] for upload in fake_minio.uploaded}
    assert buckets == {"videos", "video-frames"}


async def test_upload_marks_camera_as_has_video_on_map(
    logged_in_client, make_camera, sample_mp4
):
    camera = await make_camera()

    geojson_before = await logged_in_client.get("/api/v1/cameras/geojson")
    feature_before = next(
        f
        for f in geojson_before.json()["features"]
        if f["properties"]["id"] == str(camera.id)
    )
    assert feature_before["properties"]["has_video"] is False

    with open(sample_mp4, "rb") as f:
        await logged_in_client.post(
            "/api/v1/videos",
            data={"camera_id": str(camera.id)},
            files={"file": ("clip.mp4", f, "video/mp4")},
        )

    geojson_after = await logged_in_client.get("/api/v1/cameras/geojson")
    feature_after = next(
        f
        for f in geojson_after.json()["features"]
        if f["properties"]["id"] == str(camera.id)
    )
    assert feature_after["properties"]["has_video"] is True


async def test_list_videos_filters_by_name_search(
    logged_in_client, make_camera, sample_mp4
):
    camera = await make_camera()
    with open(sample_mp4, "rb") as f:
        await logged_in_client.post(
            "/api/v1/videos",
            data={"camera_id": str(camera.id)},
            files={"file": ("intersection.mp4", f, "video/mp4")},
        )

    response = await logged_in_client.get(
        "/api/v1/videos", params={"name_search": "intersection"}
    )
    assert response.status_code == 200
    videos = response.json()
    assert len(videos) == 1
    assert "intersection" in videos[0]["name"]

    response = await logged_in_client.get(
        "/api/v1/videos", params={"name_search": "no-such-name"}
    )
    assert response.json() == []
