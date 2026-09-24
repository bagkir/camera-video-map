import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.v1.routers.analyses import router as analyses_router
from src.api.v1.routers.auth import router as auth_router
from src.api.v1.routers.camera import router as cameras_router
from src.api.v1.routers.users import router as users_router
from src.api.v1.routers.videos import router as videos_router
from src.core.config import settings
from src.core.database import check_db_connection, dispose_engine
from src.core.exceptions import (
    register_exception_handlers,
    register_unhandled_exception_handler,
)
from src.core.logging_config import setup_logging
from src.core.minio_client import check_minio_connection, ensure_bucket
from src.core.redis_client import check_redis_connection, close_redis
from src.web.routers.pages import router as pages_router

logger = logging.getLogger(__name__)


# ========== LIFECYCLE EVENTS ==========


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager для FastAPI.

    Выполняется при:
    - startup: настройка логирования
    - shutdown: закрытие подключений к БД
    """
    setup_logging()
    if not await check_db_connection():
        logger.critical("Database is unreachable — aborting startup")
        raise RuntimeError("Database connection check failed on startup")

    if not await check_redis_connection():
        logger.warning("Redis is unreachable — camera map will fall back to DB queries")
    if not await check_minio_connection():
        logger.warning("MinIO is unreachable — video upload will fail until it's back")
    else:
        await asyncio.to_thread(ensure_bucket, settings.MINIO_BUCKET_VIDEOS)
        await asyncio.to_thread(ensure_bucket, settings.MINIO_BUCKET_FRAMES)
    logger.info("Application started")
    yield
    await close_redis()
    await dispose_engine()
    logger.info("Application stopped")


# ========== CREATE APP ==========

app = FastAPI(
    title=settings.APP_NAME,
    description="REST API для карты с камерами и видео",
    version="1.0.0",
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    lifespan=lifespan,
)

# ========== MIDDLEWARE ==========

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== EXCEPTION HANDLERS ==========

register_exception_handlers(app)
register_unhandled_exception_handler(app)

# ========== ROUTERS ==========
app.mount("/static", StaticFiles(directory="src/web/static"), name="static")
app.include_router(pages_router)
app.include_router(router=auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(router=users_router, prefix=settings.API_V1_PREFIX)
app.include_router(router=cameras_router, prefix=settings.API_V1_PREFIX)
app.include_router(router=videos_router, prefix=settings.API_V1_PREFIX)
app.include_router(router=analyses_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check(response: Response):
    """проверяет доступность БД."""
    db_ok = await check_db_connection()
    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unhealthy", "database": "unreachable"}
    return {"status": "healthy", "database": "ok"}


# Для запуска через python -m
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
