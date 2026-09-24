"""Тесты запуска и просмотра анализов видео (заглушка CV-пайплайна)."""

import uuid


async def _upload_video(client, camera_id, sample_mp4):
    with open(sample_mp4, "rb") as f:
        response = await client.post(
            "/api/v1/videos",
            data={"camera_id": str(camera_id)},
            files={"file": ("clip.mp4", f, "video/mp4")},
        )
    return response.json()


async def test_run_analysis_for_unknown_video_404(logged_in_client):
    response = await logged_in_client.post(
        f"/api/v1/videos/{uuid.uuid4()}/analyses", json={"analysis_type": "traffic"}
    )
    assert response.status_code == 404


async def test_run_and_list_analysis(logged_in_client, make_camera, sample_mp4):
    camera = await make_camera()
    video = await _upload_video(logged_in_client, camera.id, sample_mp4)

    run_response = await logged_in_client.post(
        f"/api/v1/videos/{video['id']}/analyses", json={"analysis_type": "traffic"}
    )
    assert run_response.status_code == 201
    analysis = run_response.json()
    assert analysis["analysis_type"] == "traffic"
    assert analysis["status"] == "done"
    assert "vehicle_count" in analysis["result"]

    list_response = await logged_in_client.get(f"/api/v1/videos/{video['id']}/analyses")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


async def test_camera_analyses_endpoint_lists_across_videos(
    logged_in_client, make_camera, sample_mp4
):
    camera = await make_camera()
    video = await _upload_video(logged_in_client, camera.id, sample_mp4)
    await logged_in_client.post(
        f"/api/v1/videos/{video['id']}/analyses", json={"analysis_type": "speed"}
    )

    response = await logged_in_client.get(f"/api/v1/cameras/{camera.id}/analyses")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["video_id"] == video["id"]
    assert body[0]["analysis_type"] == "speed"
