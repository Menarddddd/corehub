from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.announcement import AnnouncementRepository
from app.services.announcement import AnnouncementService


async def get_announcement_service(db: Annotated[AsyncSession, Depends(get_db)]):
    repo = AnnouncementRepository(db)
    return AnnouncementService(repo)
