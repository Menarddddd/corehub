from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository

from app.models.users import User
from app.utils.cursor import decode_cursor


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

    async def get_users(
        self,
        *conditions,
        limit: int,
        cursor: str | None,
        options: list | None = None,
    ) -> Sequence[User]:
        stmt = select(User)

        if conditions:
            stmt = stmt.where(*conditions)

        if cursor:
            decoded_cursor = decode_cursor(cursor)
            stmt = stmt.where(User.id > decoded_cursor.item_id)

        if options:
            stmt = stmt.options(*options)

        stmt = stmt.order_by(User.id.asc()).limit(limit + 1)

        result = await self.db.execute(stmt)
        return result.scalars().all()
