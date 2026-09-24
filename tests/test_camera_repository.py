"""Тесты фильтров CameraRepository (ТЗ 1.3.4)."""


async def test_get_by_camera_id(camera_repo, make_camera):
    camera = await make_camera(camera_id="cam-lookup")
    found = await camera_repo.get_by_camera_id("cam-lookup")
    assert found is not None
    assert found.id == camera.id


async def test_get_by_camera_id_missing_returns_none(camera_repo):
    assert await camera_repo.get_by_camera_id("does-not-exist") is None


async def test_list_filtered_search_by_name(camera_repo, make_camera):
    await make_camera(camera_name="Камера у метро")
    await make_camera(camera_name="Камера на набережной")

    rows = await camera_repo.list_filtered(search="метро")

    assert len(rows) == 1
    assert rows[0][0].camera_name == "Камера у метро"


async def test_list_filtered_by_model_type_class(camera_repo, make_camera):
    await make_camera(
        model="Axis P3245", camera_type="Купольная", camera_class="Обзорная"
    )
    await make_camera(
        model="Dahua IPC-HFW", camera_type="Уличная", camera_class="Пешеходная"
    )

    rows = await camera_repo.list_filtered(model="Axis P3245")
    assert {r[0].model for r in rows} == {"Axis P3245"}

    rows = await camera_repo.list_filtered(camera_type="Уличная")
    assert {r[0].camera_type for r in rows} == {"Уличная"}

    rows = await camera_repo.list_filtered(camera_class="Обзорная")
    assert {r[0].camera_class for r in rows} == {"Обзорная"}


async def test_list_filtered_video_count_range(
    camera_repo, make_camera, video_repo, make_user
):
    camera_no_videos = await make_camera(camera_name="Без видео")
    camera_with_videos = await make_camera(camera_name="С видео")
    author = await make_user()

    for _ in range(3):
        await video_repo.create(
            name="v",
            camera_id=camera_with_videos.id,
            author_id=author.id,
            file_key="k",
        )

    rows = await camera_repo.list_filtered(videos_from=1)
    ids = {r[0].id for r in rows}
    assert camera_with_videos.id in ids
    assert camera_no_videos.id not in ids

    rows = await camera_repo.list_filtered(videos_to=0)
    ids = {r[0].id for r in rows}
    assert camera_no_videos.id in ids
    assert camera_with_videos.id not in ids

    row = next(r for r in rows if r[0].id == camera_no_videos.id)
    assert row[1] == 0


async def test_get_by_id_with_video_count(camera_repo, make_camera):
    camera = await make_camera()
    row = await camera_repo.get_by_id_with_video_count(camera.id)
    assert row is not None
    assert row[0].id == camera.id
    assert row[1] == 0


async def test_list_all_with_video_count(camera_repo, make_camera):
    await make_camera()
    await make_camera()
    rows = await camera_repo.list_all_with_video_count()
    assert len(rows) == 2
