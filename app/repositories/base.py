from typing import Generic, Sequence, TypeVar
from uuid import UUID
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base
from app.utils.cursor import decode_cursor

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    def __init__(self, db: AsyncSession, model):
        self.db = db
        self.model = model

    async def get_by_id(self, id: UUID, *options) -> T | None:
        stmt = select(self.model).where(self.model.id == id)
        if options:
            stmt = stmt.options(*options)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def save(self, obj: T) -> T:
        try:
            self.db.add(obj)
            await self.db.commit()
            await self.db.refresh(obj)
            return obj
        except Exception:
            await self.db.rollback()
            raise

    async def update(self, obj: T) -> T:
        try:
            await self.db.commit()
            await self.db.refresh(obj)
            return obj
        except Exception:
            await self.db.rollback()
            raise

    async def delete(self, obj: T) -> None:
        try:
            await self.db.delete(obj)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

    async def get_many(
        self,
        *conditions,
        limit: int,
        cursor: str | None = None,
        options: list | None = None,
    ) -> Sequence[T]:
        stmt = select(self.model)

        if conditions:
            stmt = stmt.where(*conditions)

        if cursor:
            decoded_cursor = decode_cursor(cursor)
            stmt = stmt.where(
                or_(
                    self.model.created_at < decoded_cursor.created_at,
                    and_(
                        self.model.created_at == decoded_cursor.created_at,
                        self.model.id > decoded_cursor.item_id,
                    ),
                ),
            )

        if options:
            stmt = stmt.options(*options)

        stmt = stmt.order_by(self.model.created_at.desc(), self.model.id.asc()).limit(
            limit + 1
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()
