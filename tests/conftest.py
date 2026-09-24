"""
Общие фикстуры для тестов.

DATABASE_URL и прочие обязательные настройки выставляются в os.environ ДО
любого импорта src.* — Settings читается один раз при импорте
src.core.config (lru_cache), поэтому порядок здесь важен.
Тесты рассчитаны на одноразовый Postgres в Docker, например:

    docker run -d --name camtest-pg -e POSTGRES_USER=test \\
        -e POSTGRES_PASSWORD=test -e POSTGRES_DB=test \\
        -p 15432:5432 postgres:15-alpine

Переопределить адрес БД можно через переменную окружения TEST_DATABASE_URL.
"""

import os

os.environ.setdefault(
    "DATABASE_URL",
    os.environ.get(
        "TEST_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:15432/test"
    ),
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("MINIO_ACCESS_KEY", "test-access-key")
os.environ.setdefault("MINIO_SECRET_KEY", "test-secret-key")
os.environ.setdefault("MINIO_ENDPOINT", "localhost:9000")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("ENVIRONMENT", "development")

import subprocess  # noqa: E402
import uuid  # noqa: E402
from collections.abc import AsyncIterator  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any  # noqa: E402

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import event  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker  # noqa: E402

import src.data.models  # noqa: E402,F401  регистрирует все модели в Base.metadata
import src.domain.services.video as video_service_module  # noqa: E402
from src.core.database import Base, engine, get_db  # noqa: E402
from src.core.redis_client import get_redis_client  # noqa: E402
from src.data.models.camera import Camera  # noqa: E402
from src.data.models.user import User  # noqa: E402
from src.data.repositories.analysis_repository import AnalysisRepository  # noqa: E402
from src.data.repositories.camera_repository import CameraRepository  # noqa: E402
from src.data.repositories.user_repository import UserRepository  # noqa: E402
from src.data.repositories.video_repository import VideoRepository  # noqa: E402
from src.utils.securitry import get_password_hash  # noqa: E402


class FakeRedis:
    """Минимальная замена redis.asyncio.Redis для тестов (без сети)."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._store[key] = value

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def ping(self) -> bool:
        return True


class FakeMinioClient:
    """Замена MinIO-клиента: fput_object пишет только в память."""

    def __init__(self) -> None:
        self.uploaded: list[tuple[str, str, str]] = []

    def fput_object(self, bucket: str, key: str, path: str, content_type: str) -> None:
        self.uploaded.append((bucket, key, content_type))


@pytest.fixture(autouse=True)
def fake_minio(monkeypatch: pytest.MonkeyPatch) -> FakeMinioClient:
    """
    Подменяет MinIO-клиент во всех тестах (autouse) — VideoService.upload
    никогда не должен реально стучаться в MinIO. Тесты, которым нужен доступ
    к списку загруженных файлов, просто запрашивают эту фикстуру как аргумент.
    """
    fake = FakeMinioClient()
    monkeypatch.setattr(video_service_module, "get_minio_client", lambda: fake)
    return fake


@pytest_asyncio.fixture(scope="session")
async def _tables() -> AsyncIterator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(_tables: None) -> AsyncIterator[AsyncSession]:
    """
    Сессия в отдельном SAVEPOINT на подключение — откатывается после
    каждого теста, независимо от того, сколько раз тестируемый код
    вызвал commit()/rollback() (см. get_db()).
    """
    async with engine.connect() as conn:
        outer_trans = await conn.begin()
        session_factory = async_sessionmaker(
            bind=conn, expire_on_commit=False, class_=AsyncSession
        )
        session = session_factory()

        nested = await conn.begin_nested()

        @event.listens_for(session.sync_session, "after_transaction_end")
        def _restart_savepoint(sess: Any, transaction: Any) -> None:
            nonlocal nested
            if not nested.is_active:
                nested = conn.sync_connection.begin_nested()

        try:
            yield session
        finally:
            await session.close()
            await outer_trans.rollback()


@pytest_asyncio.fixture
async def fake_redis() -> FakeRedis:
    return FakeRedis()


@pytest_asyncio.fixture
async def app(db_session: AsyncSession, fake_redis: FakeRedis):
    from main import app as fastapi_app

    async def _get_db_override() -> AsyncIterator[AsyncSession]:
        yield db_session

    fastapi_app.dependency_overrides[get_db] = _get_db_override
    fastapi_app.dependency_overrides[get_redis_client] = lambda: fake_redis

    yield fastapi_app

    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app: Any) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def logged_in_client(client: AsyncClient) -> AsyncClient:
    """HTTP-клиент с уже залогиненным пользователем (куки в cookie jar)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dashboard-user@example.com",
            "full_name": "Dashboard User",
            "password": "password123",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "dashboard-user@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    return client


@pytest_asyncio.fixture
async def user_repo(db_session: AsyncSession) -> UserRepository:
    return UserRepository(db_session)


@pytest_asyncio.fixture
async def camera_repo(db_session: AsyncSession) -> CameraRepository:
    return CameraRepository(db_session)


@pytest_asyncio.fixture
async def video_repo(db_session: AsyncSession) -> VideoRepository:
    return VideoRepository(db_session)


@pytest_asyncio.fixture
async def analysis_repo(db_session: AsyncSession) -> AnalysisRepository:
    return AnalysisRepository(db_session)


@pytest_asyncio.fixture
async def make_user(user_repo: UserRepository):
    async def _make_user(
        email: str = "user@example.com",
        full_name: str = "Test User",
        password: str = "password123",
    ) -> User:
        return await user_repo.create(
            email=email,
            full_name=full_name,
            password_hash=get_password_hash(password),
        )

    return _make_user


@pytest_asyncio.fixture
async def make_camera(camera_repo: CameraRepository):
    async def _make_camera(**overrides: Any) -> Camera:
        defaults: dict[str, Any] = dict(
            id=uuid.uuid4(),
            camera_id=f"cam-{uuid.uuid4().hex[:8]}",
            camera_name="Камера на Тверской",
            camera_place="ул. Тверская, д. 1",
            model="Hikvision DS-2CD2",
            camera_type="Уличная",
            camera_class="Транспортная",
            camera_latitude=55.75,
            camera_longitude=37.62,
            archive=False,
        )
        defaults.update(overrides)
        return await camera_repo.create(**defaults)

    return _make_camera


@pytest_asyncio.fixture
async def make_video(video_repo: VideoRepository):
    async def _make_video(*, camera_id: Any, author_id: Any, **overrides: Any) -> Any:
        defaults: dict[str, Any] = dict(
            id=uuid.uuid4(),
            name=f"video-{uuid.uuid4().hex[:8]}.mp4",
            camera_id=camera_id,
            author_id=author_id,
            file_key=f"{camera_id}/source.mp4",
        )
        defaults.update(overrides)
        return await video_repo.create(**defaults)

    return _make_video


@pytest.fixture(scope="session")
def sample_mp4(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Небольшой валидный mp4, сгенерированный ffmpeg (без сети)."""
    path = tmp_path_factory.mktemp("media") / "sample.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=1:size=320x240:rate=10",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return path


@pytest.fixture
def broken_mp4(tmp_path: Path) -> Path:
    """Файл с расширением .mp4, который не является видео."""
    path = tmp_path / "broken.mp4"
    path.write_bytes(b"not a real video file")
    return path
