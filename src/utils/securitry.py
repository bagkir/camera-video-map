from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi.responses import Response
from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.config import settings
from src.core.exceptions import UnauthorizedException
from src.data.models.user import User


def create_tokens(data: dict[str, Any]) -> dict[str, str]:
    # Текущее время в UTC
    now = datetime.now(timezone.utc)

    # AccessToken - 30 минут
    access_expire = now + timedelta(minutes=30)
    access_payload = data.copy()
    access_payload.update({"exp": int(access_expire.timestamp()), "type": "access"})
    access_token = jwt.encode(
        access_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    # RefreshToken - 7 дней
    refresh_expire = now + timedelta(days=7)
    refresh_payload = data.copy()
    refresh_payload.update({"exp": int(refresh_expire.timestamp()), "type": "refresh"})
    refresh_token = jwt.encode(
        refresh_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return {"access_token": access_token, "refresh_token": refresh_token}


async def authenticate_user(user: User | None, password: str) -> User | None:
    if user is None or not verify_password(
        plain_password=password, hashed_password=user.password_hash
    ):
        return None
    return user


def set_tokens(response: Response, user_id: int) -> None:
    new_tokens = create_tokens(data={"sub": str(user_id)})

    response.set_cookie(
        key="user_access_token",
        value=new_tokens["access_token"],
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
    )

    response.set_cookie(
        key="user_refresh_token",
        value=new_tokens["refresh_token"],
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
    )


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def decode_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except JWTError as exc:
        raise UnauthorizedException("Invalid or expired token") from exc

    if payload.get("type") != expected_type:
        raise UnauthorizedException("Invalid token type")

    return payload
