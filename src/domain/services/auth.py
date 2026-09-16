from src.core.exceptions import AlreadyExistsException, UnauthorizedException
from src.data.models.user import User
from src.data.repositories.user_repository import UserRepository
from src.utils.securitry import authenticate_user, decode_token, get_password_hash


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def register(self, email: str, full_name: str, password: str) -> User:
        if await self.user_repository.get_by_email(email):
            raise AlreadyExistsException("User", email)

        return await self.user_repository.create(
            email=email,
            full_name=full_name,
            password_hash=get_password_hash(password),
        )

    async def login(self, email: str, password: str) -> User:
        user = await self.user_repository.get_by_email(email)
        user = await authenticate_user(user, password)
        if user is None:
            raise UnauthorizedException("Invalid email or password")
        return user

    async def get_user_from_refresh(self, refresh_token: str) -> User:
        payload = decode_token(refresh_token, expected_type="refresh")
        user_id = int(payload["sub"])
        user = await self.user_repository.get_by_id(user_id)
        if user is None:
            raise UnauthorizedException("User not found")
        return user

    async def get_user_from_access(self, access_token: str) -> User:
        payload = decode_token(access_token, expected_type="access")
        user_id = int(payload["sub"])
        user = await self.user_repository.get_by_id(user_id)
        if user is None:
            raise UnauthorizedException("User not found")
        return user
