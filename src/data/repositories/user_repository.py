from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.user import User
from src.data.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(self.model).where(self.model.email == email)
        )
        return result.scalar_one_or_none()
