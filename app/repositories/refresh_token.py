from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.refresh_tokens import RefreshToken
from app.repositories.base import BaseRepository


class RefreshRepository(BaseRepository[RefreshToken]):

    def __init__(self, db: AsyncSession):
        super().__init__(db, RefreshToken)

    async def get_refresh_token(self, hashed_token: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.hashed_token == hashed_token)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
