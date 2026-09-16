from fastapi import APIRouter, Request, Response, status

from src.api.v1.dependencies import AuthServiceDep, CurrentUserDep
from src.api.v1.schemas.user import UserLoginRequest, UserOut, UserRegisterRequest
from src.core.exceptions import UnauthorizedException
from src.utils.securitry import set_tokens

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegisterRequest, auth_service: AuthServiceDep):
    return await auth_service.register(
        email=data.email, full_name=data.full_name, password=data.password
    )


@router.post("/login", response_model=UserOut)
async def login(
    data: UserLoginRequest, response: Response, auth_service: AuthServiceDep
):
    user = await auth_service.login(data.email, data.password)
    set_tokens(response, user.id)
    return user


@router.post("/refresh")
async def refresh(request: Request, response: Response, auth_service: AuthServiceDep):
    refresh_token = request.cookies.get("user_refresh_token")
    if not refresh_token:
        raise UnauthorizedException("No refresh token")
    user = await auth_service.get_user_from_refresh(refresh_token)
    set_tokens(response, user.id)
    return {"detail": "Tokens refreshed"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("user_access_token")
    response.delete_cookie("user_refresh_token")
    return {"detail": "Logged out"}


@router.get("/me", response_model=UserOut)
async def me(current_user: CurrentUserDep):
    return current_user
