import asyncio
import logging

from minio import Minio

from src.core.config import settings

logger = logging.getLogger(__name__)

_minio_client: Minio | None = None


def get_minio_client() -> Minio:
    global _minio_client
    if _minio_client is None:
        _minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
    return _minio_client


def ensure_bucket(bucket: str) -> None:
    client = get_minio_client()
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        logger.info("Created MinIO bucket: %s", bucket)


async def check_minio_connection() -> bool:
    try:
        await asyncio.to_thread(get_minio_client().list_buckets)
        return True
    except Exception:
        logger.exception("MinIO connection check failed")
        return False
