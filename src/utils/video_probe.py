import asyncio
import json


async def probe_video(path: str) -> dict:
    """
    Проверка читаемости файла (ТЗ 1.3.3: "проверка чтения файла") +
    извлечение duration/resolution/fps для полей видео (ТЗ 2.2.1).
    Бросает ValueError, если файл не парсится как видео или в нём нет видеопотока —
    это и есть проверка "на самом деле читается", а не просто расширение .mp4.
    """
    proc = await asyncio.create_subprocess_exec(
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise ValueError(stderr.decode(errors="ignore").strip() or "ffprobe failed")

    data = json.loads(stdout)
    video_streams = [
        s for s in data.get("streams", []) if s.get("codec_type") == "video"
    ]
    if not video_streams:
        raise ValueError("В файле не найден видеопоток")

    stream = video_streams[0]
    fmt = data.get("format", {})

    fps = None
    rate = stream.get("r_frame_rate")  # формат "30/1"
    if rate:
        num, _, den = rate.partition("/")
        try:
            fps = round(int(num) / int(den or 1))
        except (ValueError, ZeroDivisionError):
            fps = None

    return {
        "duration_seconds": int(float(fmt.get("duration", 0))),
        "resolution_width": stream.get("width"),
        "resolution_height": stream.get("height"),
        "fps": fps,
    }


async def extract_first_frame(video_path: str, output_path: str) -> None:
    """Сохранение первого кадра (ТЗ 1.3.5)."""
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vframes",
        "1",
        "-q:v",
        "2",
        output_path,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise ValueError(stderr.decode(errors="ignore").strip() or "ffmpeg failed")
