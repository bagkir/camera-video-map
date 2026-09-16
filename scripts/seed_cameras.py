"""
Заполняет d_camera тестовыми данными (ТЗ, раздел 1: "добавить рандомные
значения для теста").

Запуск:
    poetry run python -m scripts.seed_cameras --count 50
"""

import argparse
import asyncio
import random
import uuid

from src.core.database import async_session_maker
from src.data.models.camera import Camera

CAMERA_CLASSES = [(1, "Обзорная"), (2, "Транспортная"), (3, "Пешеходная")]
CAMERA_TYPES = [(1, "Купольная"), (2, "Уличная"), (3, "Скрытая")]
CAMERA_MODELS = ["Hikvision DS-2CD2", "Dahua IPC-HFW", "Axis P3245", "Trassir TR-D"]

LAT_RANGE = (55.5, 56.0)
LON_RANGE = (37.3, 37.9)


def _rand_camera(idx: int) -> dict:
    class_cd, class_name = random.choice(CAMERA_CLASSES)
    type_cd, type_name = random.choice(CAMERA_TYPES)
    return dict(
        id=uuid.uuid4(),
        camera_id=f"{idx:03d}-{uuid.uuid4().hex[:6]}",  # гарантированно уникален
        camera_class_cd=class_cd,
        camera_class=class_name,
        model=random.choice(CAMERA_MODELS),
        camera_name=f"Камера №{idx}",
        camera_place=f"ул. Тестовая, д. {random.randint(1, 100)}",
        camera_place_cd=random.randint(1000, 9999),
        serial_number=f"SN{random.randint(100000, 999999)}",
        camera_type_cd=type_cd,
        camera_type=type_name,
        camera_latitude=round(random.uniform(*LAT_RANGE), 6),
        camera_longitude=round(random.uniform(*LON_RANGE), 6),
        archive=random.random() < 0.1,
        azimuth=random.randint(0, 359),
    )


async def seed(count: int) -> None:
    async with async_session_maker() as session:
        session.add_all(Camera(**_rand_camera(i)) for i in range(1, count + 1))
        await session.commit()
    print(f"Добавлено {count} тестовых камер")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=50)
    args = parser.parse_args()
    asyncio.run(seed(args.count))
