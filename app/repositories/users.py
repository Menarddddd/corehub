from uuid import UUID
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository

from app.models.users import User


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, User)

    async def _get_user(self, condition, *options) -> User | None:
        stmt = select(User).where(condition)
        if options:
            stmt = stmt.options(*options)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str, *options) -> User | None:
        return await self._get_user(User.username == username, *options)

    async def get_by_email(self, email: str, *options) -> User | None:
        return await self._get_user(User.email == email, *options)

    async def get_by_department(self, department_id: UUID) -> Sequence[User]:
        stmt = select(User).where(User.department_id == department_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_role(self, role: str) -> Sequence[User]:
        stmt = select(User).where(User.role == role)
        result = await self.db.execute(stmt)
        return result.scalars().all()
