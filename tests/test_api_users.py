"""Тесты Личного кабинета (ТЗ: инфо о пользователе + последние видео)."""

import uuid

import pytest

import src.domain.services.video as video_service_module


class _FakeMinioClient:
    def fput_object(self, bucket: str, key: str, path: str, content_type: str) -> None:
        pass


@pytest.fixture(autouse=True)
def fake_minio(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        video_service_module, "get_minio_client", lambda: _FakeMinioClient()
    )


async def test_dashboard_requires_authentication(client):
    response = await client.get("/api/v1/users/me/dashboard")
    assert response.status_code == 401


async def test_dashboard_empty_for_new_user(logged_in_client):
    response = await logged_in_client.get("/api/v1/users/me/dashboard")
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == "dashboard-user@example.com"
    assert body["recent_videos"] == []


async def test_dashboard_shows_uploaded_video(
    logged_in_client, make_camera, sample_mp4
):
    camera = await make_camera()
    with open(sample_mp4, "rb") as f:
        await logged_in_client.post(
            "/api/v1/videos",
            data={"camera_id": str(camera.id)},
            files={"file": ("clip.mp4", f, "video/mp4")},
        )

    response = await logged_in_client.get("/api/v1/users/me/dashboard")
    body = response.json()
    assert len(body["recent_videos"]) == 1
    assert body["recent_videos"][0]["camera_id"] == str(camera.id)


async def test_list_users_requires_authentication(client):
    response = await client.get("/api/v1/users")
    assert response.status_code == 401


async def test_list_users_visible_to_any_authenticated_user(logged_in_client):
    """ТЗ: ролевой модели нет, все пользователи равны."""
    response = await logged_in_client.get("/api/v1/users")
    assert response.status_code == 200
    emails = {u["email"] for u in response.json()}
    assert "dashboard-user@example.com" in emails


async def test_camera_not_found_returns_404(logged_in_client):
    response = await logged_in_client.get(f"/api/v1/cameras/{uuid.uuid4()}")
    assert response.status_code == 404
