from src.data.models import User
from src.data.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def get_all(self) -> list[User]:
        return await self.user_repository.get_all()
