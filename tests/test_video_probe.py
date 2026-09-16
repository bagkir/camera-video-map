"""
Тесты src/utils/video_probe.py на реальных вызовах ffmpeg/ffprobe
(ТЗ 1.3.3: "проверка чтения файла").
"""

from pathlib import Path

import pytest

from src.utils.video_probe import extract_first_frame, probe_video


async def test_probe_video_reads_real_metadata(sample_mp4: Path):
    metadata = await probe_video(str(sample_mp4))

    assert metadata["duration_seconds"] == 1
    assert metadata["resolution_width"] == 320
    assert metadata["resolution_height"] == 240
    assert metadata["fps"] == 10


async def test_probe_video_rejects_broken_file(broken_mp4: Path):
    with pytest.raises(ValueError):
        await probe_video(str(broken_mp4))


async def test_probe_video_rejects_missing_file(tmp_path: Path):
    with pytest.raises(ValueError):
        await probe_video(str(tmp_path / "does-not-exist.mp4"))


async def test_extract_first_frame_writes_image(sample_mp4: Path, tmp_path: Path):
    frame_path = tmp_path / "frame.jpg"
    await extract_first_frame(str(sample_mp4), str(frame_path))

    assert frame_path.exists()
    assert frame_path.stat().st_size > 0


async def test_extract_first_frame_rejects_broken_file(
    broken_mp4: Path, tmp_path: Path
):
    frame_path = tmp_path / "frame.jpg"
    with pytest.raises(ValueError):
        await extract_first_frame(str(broken_mp4), str(frame_path))
