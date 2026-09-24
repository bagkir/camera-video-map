"""
Тесты auth-flow (ТЗ: регистрация email/ФИО/пароль, хранение хешем, JWT +
Refresh token).
"""

from datetime import datetime, timedelta, timezone

from jose import jwt

from src.core.config import settings


def _make_token(*, type_: str, expired: bool = False) -> str:
    now = datetime.now(timezone.utc)
    expire = now - timedelta(minutes=1) if expired else now + timedelta(minutes=30)
    payload = {"sub": "1", "type": type_, "exp": int(expire.timestamp())}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def test_register_creates_user(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@example.com",
            "full_name": "New User",
            "password": "password123",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert body["full_name"] == "New User"
    assert "password" not in body
    assert "password_hash" not in body


async def test_register_duplicate_email_conflicts(client):
    payload = {
        "email": "dup@example.com",
        "full_name": "First",
        "password": "password123",
    }
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post(
        "/api/v1/auth/register", json={**payload, "full_name": "Second"}
    )
    assert second.status_code == 409


async def test_register_rejects_short_password(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "weak@example.com", "full_name": "Weak", "password": "short"},
    )
    assert response.status_code == 422


async def test_login_success_sets_cookies(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "full_name": "Login",
            "password": "password123",
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    assert "user_access_token" in response.cookies
    assert "user_refresh_token" in response.cookies


async def test_login_wrong_password_unauthorized(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrongpw@example.com",
            "full_name": "X",
            "password": "password123",
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpw@example.com", "password": "not-the-password"},
    )
    assert response.status_code == 401


async def test_login_unknown_user_unauthorized(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@example.com", "password": "password123"},
    )
    assert response.status_code == 401


async def test_me_requires_authentication(client):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_me_returns_current_user(logged_in_client):
    response = await logged_in_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == "dashboard-user@example.com"


async def test_refresh_issues_usable_access_token(logged_in_client):
    response = await logged_in_client.post("/api/v1/auth/refresh")
    assert response.status_code == 200
    assert logged_in_client.cookies.get("user_access_token")

    me_response = await logged_in_client.get("/api/v1/auth/me")
    assert me_response.status_code == 200


async def test_refresh_without_cookie_unauthorized(client):
    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 401


async def test_logout_clears_session(logged_in_client):
    await logged_in_client.post("/api/v1/auth/logout")

    response = await logged_in_client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_me_rejects_expired_access_token(client):
    client.cookies.set("user_access_token", _make_token(type_="access", expired=True))
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_me_rejects_tampered_token(client):
    client.cookies.set("user_access_token", "not.a.valid.jwt")
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_me_rejects_refresh_token_used_as_access(client):
    """Токен валиден и не просрочен, но его type != "access" — не должен приниматься."""
    client.cookies.set("user_access_token", _make_token(type_="refresh"))
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_refresh_rejects_access_token_used_as_refresh(client):
    client.cookies.set("user_refresh_token", _make_token(type_="access"))
    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 401


async def test_refresh_rejects_expired_refresh_token(client):
    client.cookies.set("user_refresh_token", _make_token(type_="refresh", expired=True))
    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 401
