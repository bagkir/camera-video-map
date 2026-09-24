"""Тесты фильтров VideoRepository (ТЗ 2.3.5) и Личного кабинета."""

from datetime import datetime, timedelta, timezone

from src.data.models.analysis import AnalysisStatus, AnalysisType
from src.data.models.video import TimeOfDay, TracingStatus


async def test_list_filtered_by_camera(video_repo, make_camera, make_user, make_video):
    camera_a = await make_camera()
    camera_b = await make_camera()
    author = await make_user()
    await make_video(camera_id=camera_a.id, author_id=author.id)
    await make_video(camera_id=camera_b.id, author_id=author.id)

    videos = await video_repo.list_filtered(camera_id=camera_a.id)

    assert len(videos) == 1
    assert videos[0].camera_id == camera_a.id


async def test_list_filtered_name_search(
    video_repo, make_camera, make_user, make_video
):
    camera = await make_camera()
    author = await make_user()
    await make_video(
        camera_id=camera.id, author_id=author.id, name="Перекресток утро.mp4"
    )
    await make_video(camera_id=camera.id, author_id=author.id, name="Двор вечер.mp4")

    videos = await video_repo.list_filtered(name_search="перекресток")

    assert len(videos) == 1
    assert "Перекресток" in videos[0].name


async def test_list_filtered_author_search(
    video_repo, make_camera, make_user, make_video
):
    camera = await make_camera()
    alice = await make_user(email="alice@example.com", full_name="Алиса Иванова")
    bob = await make_user(email="bob@example.com", full_name="Боб Петров")
    await make_video(camera_id=camera.id, author_id=alice.id)
    await make_video(camera_id=camera.id, author_id=bob.id)

    videos = await video_repo.list_filtered(author_search="иванова")

    assert len(videos) == 1
    assert videos[0].author_id == alice.id


async def test_list_filtered_by_tracing_status_and_time_of_day(
    video_repo, make_camera, make_user, make_video
):
    camera = await make_camera()
    author = await make_user()
    await make_video(
        camera_id=camera.id,
        author_id=author.id,
        tracing_status=TracingStatus.DONE,
        time_of_day=TimeOfDay.NIGHT,
    )
    await make_video(
        camera_id=camera.id,
        author_id=author.id,
        tracing_status=TracingStatus.ERROR,
        time_of_day=TimeOfDay.DAY,
    )

    videos = await video_repo.list_filtered(tracing_status=TracingStatus.DONE)
    assert len(videos) == 1
    assert videos[0].tracing_status == TracingStatus.DONE

    videos = await video_repo.list_filtered(time_of_day=TimeOfDay.NIGHT)
    assert len(videos) == 1
    assert videos[0].time_of_day == TimeOfDay.NIGHT


async def test_list_filtered_duration_range(
    video_repo, make_camera, make_user, make_video
):
    camera = await make_camera()
    author = await make_user()
    await make_video(camera_id=camera.id, author_id=author.id, duration_seconds=10)
    await make_video(camera_id=camera.id, author_id=author.id, duration_seconds=100)

    videos = await video_repo.list_filtered(duration_from=50)
    assert {v.duration_seconds for v in videos} == {100}

    videos = await video_repo.list_filtered(duration_to=50)
    assert {v.duration_seconds for v in videos} == {10}


async def test_get_last_by_author_orders_by_uploaded_at_desc(
    video_repo, make_camera, make_user, make_video
):
    camera = await make_camera()
    author = await make_user()
    # now() внутри одной транзакции постоянен (transaction_timestamp), поэтому
    # время загрузки задаём явно, а не полагаемся на server_default.
    now = datetime.now(timezone.utc)
    first = await make_video(
        camera_id=camera.id,
        author_id=author.id,
        name="first.mp4",
        uploaded_at=now - timedelta(minutes=1),
    )
    second = await make_video(
        camera_id=camera.id, author_id=author.id, name="second.mp4", uploaded_at=now
    )

    videos = await video_repo.get_last_by_author(author.id, limit=5)

    assert [v.id for v in videos] == [second.id, first.id]


async def test_video_counter_zero_without_analyses(
    video_repo, make_camera, make_user, make_video
):
    camera = await make_camera()
    author = await make_user()
    await make_video(camera_id=camera.id, author_id=author.id)

    # list_filtered() эагерно подгружает analyses (см. VideoRepository) —
    # именно так .counter используется в реальных запросах API.
    [video] = await video_repo.list_filtered(camera_id=camera.id)
    assert video.counter == 0


async def test_video_counter_reflects_analyses(
    video_repo, analysis_repo, make_camera, make_user, make_video
):
    camera = await make_camera()
    author = await make_user()
    video = await make_video(camera_id=camera.id, author_id=author.id)
    await analysis_repo.create(
        video_id=video.id,
        analysis_type=AnalysisType.TRAFFIC,
        status=AnalysisStatus.DONE,
    )

    [reloaded] = await video_repo.list_filtered(camera_id=camera.id)
    assert reloaded.counter == 1
