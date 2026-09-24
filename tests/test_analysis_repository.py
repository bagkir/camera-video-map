"""Тесты AnalysisRepository: выборка по видео и по камере."""

from src.data.models.analysis import AnalysisStatus, AnalysisType


async def test_get_by_video(
    analysis_repo, video_repo, make_camera, make_user, make_video
):
    camera = await make_camera()
    author = await make_user()
    video = await make_video(camera_id=camera.id, author_id=author.id)

    await analysis_repo.create(
        video_id=video.id,
        analysis_type=AnalysisType.TRAFFIC,
        status=AnalysisStatus.DONE,
    )
    await analysis_repo.create(
        video_id=video.id, analysis_type=AnalysisType.SPEED, status=AnalysisStatus.RUN
    )

    analyses = await analysis_repo.get_by_video(video.id)
    assert len(analyses) == 2


async def test_list_by_camera_filters_by_type_and_status(
    analysis_repo, make_camera, make_user, make_video
):
    camera_a = await make_camera()
    camera_b = await make_camera()
    author = await make_user()
    video_a = await make_video(camera_id=camera_a.id, author_id=author.id)
    video_b = await make_video(camera_id=camera_b.id, author_id=author.id)

    await analysis_repo.create(
        video_id=video_a.id,
        analysis_type=AnalysisType.TRAFFIC,
        status=AnalysisStatus.DONE,
    )
    await analysis_repo.create(
        video_id=video_a.id,
        analysis_type=AnalysisType.SPEED,
        status=AnalysisStatus.ERROR,
    )
    await analysis_repo.create(
        video_id=video_b.id,
        analysis_type=AnalysisType.TRAFFIC,
        status=AnalysisStatus.DONE,
    )

    by_camera = await analysis_repo.list_by_camera(camera_id=camera_a.id)
    assert {a.video_id for a in by_camera} == {video_a.id}
    assert len(by_camera) == 2

    by_type = await analysis_repo.list_by_camera(
        camera_id=camera_a.id, analysis_type=AnalysisType.TRAFFIC
    )
    assert len(by_type) == 1
    assert by_type[0].analysis_type == AnalysisType.TRAFFIC

    by_status = await analysis_repo.list_by_camera(
        camera_id=camera_a.id, status=AnalysisStatus.ERROR
    )
    assert len(by_status) == 1
    assert by_status[0].status == AnalysisStatus.ERROR
