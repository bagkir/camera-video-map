"""Тесты src/utils/securitry.py: хеширование паролей и JWT-токены."""

from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from src.core.config import settings
from src.core.exceptions import UnauthorizedException
from src.data.models.user import User
from src.utils.securitry import (
    authenticate_user,
    create_tokens,
    decode_token,
    get_password_hash,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = get_password_hash("s3cret-password")
    assert hashed != "s3cret-password"
    assert verify_password("s3cret-password", hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_create_tokens_contains_expected_claims():
    tokens = create_tokens({"sub": "42"})
    access_payload = jwt.decode(
        tokens["access_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    refresh_payload = jwt.decode(
        tokens["refresh_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    assert access_payload["sub"] == "42"
    assert access_payload["type"] == "access"
    assert refresh_payload["type"] == "refresh"
    assert refresh_payload["exp"] > access_payload["exp"]


def test_decode_token_round_trip():
    tokens = create_tokens({"sub": "7"})
    payload = decode_token(tokens["access_token"], expected_type="access")
    assert payload["sub"] == "7"


def test_decode_token_rejects_wrong_type():
    tokens = create_tokens({"sub": "7"})
    with pytest.raises(UnauthorizedException):
        decode_token(tokens["access_token"], expected_type="refresh")


def test_decode_token_rejects_garbage():
    with pytest.raises(UnauthorizedException):
        decode_token("not-a-real-token")


def test_decode_token_rejects_expired():
    expired_payload = {
        "sub": "1",
        "type": "access",
        "exp": int((datetime.now(timezone.utc) - timedelta(minutes=1)).timestamp()),
    }
    expired_token = jwt.encode(
        expired_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    with pytest.raises(UnauthorizedException):
        decode_token(expired_token)


async def test_authenticate_user_success():
    user = User(
        id=1, email="a@b.com", full_name="A", password_hash=get_password_hash("pw")
    )
    result = await authenticate_user(user, "pw")
    assert result is user


async def test_authenticate_user_wrong_password():
    user = User(
        id=1, email="a@b.com", full_name="A", password_hash=get_password_hash("pw")
    )
    assert await authenticate_user(user, "wrong") is None


async def test_authenticate_user_no_user():
    assert await authenticate_user(None, "pw") is None
