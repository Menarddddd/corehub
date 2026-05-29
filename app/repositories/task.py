from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository

from app.models.tasks import Task


class TaskRepository(BaseRepository[Task]):

    def __init__(self, db: AsyncSession):
        super().__init__(db, Task)

    async def get_tasks(
        self, *conditions, limit: int, cursor: str | None, options: list | None = None
    ) -> Sequence[Task]:
        return await self.get_many(
            *conditions, limit=limit, cursor=cursor, options=options
        )
