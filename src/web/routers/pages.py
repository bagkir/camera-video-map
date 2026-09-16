from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from src.api.v1.dependencies import AuthServiceDep
from src.data.models import User
from src.domain.services.auth import AuthService

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="src/web/templates")


async def get_optional_user(request: Request, auth_service: AuthService) -> User | None:
    """
    Не путать с get_current_user из dependencies.py: та версия для JSON API —
    кидает 401 при отсутствии/невалидности токена. Здесь же 401 — не ошибка,
    а сигнал "покажи страницу логина", поэтому исключение гасим.
    """
    token = request.cookies.get("user_access_token")
    if not token:
        return None
    try:
        return await auth_service.get_user_from_access(token)
    except Exception:
        return None


@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@router.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html")


@router.get("/")
async def map_page(request: Request, auth_service: AuthServiceDep):
    user = await get_optional_user(request, auth_service)
    if user is None:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse(request, "map.html", {"user": user})


@router.get("/dashboard")
async def dashboard_page(request: Request, auth_service: AuthServiceDep):
    user = await get_optional_user(request, auth_service)
    if user is None:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse(request, "dashboard.html", {"user": user})


@router.get("/cameras/{camera_id}")
async def camera_detail_page(
    camera_id: str, request: Request, auth_service: AuthServiceDep
):
    user = await get_optional_user(request, auth_service)
    if user is None:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse(
        request, "camera_detail.html", {"user": user, "camera_id": camera_id}
    )
