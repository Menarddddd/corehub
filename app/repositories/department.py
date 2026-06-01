from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository

from app.models.departments import Department


class DepartmentRepository(BaseRepository[Department]):

    def __init__(self, db: AsyncSession):
        super().__init__(db, Department)

    async def get_departments(
        self, *conditions, limit: int, cursor: str | None, options: list | None = None
    ) -> Sequence[Department]:
        return await self.get_many(
            *conditions, limit=limit, cursor=cursor, options=options
        )
