from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import FieldNotFoundException, ForbiddenException
from app.core.security import get_current_user
from app.models.announcements import Announcement
from app.models.users import User
from app.repositories.announcement import AnnouncementRepository
from app.services.announcement import AnnouncementService


async def get_announcement_service(db: Annotated[AsyncSession, Depends(get_db)]):
    repo = AnnouncementRepository(db)
    return AnnouncementService(repo)


async def check_announcement_owner(
    announcement_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Announcement:
    repo = AnnouncementRepository(db)

    announcement = await repo.get_by_id(announcement_id)

    if not announcement:
        raise FieldNotFoundException("announcements", str(announcement_id))

    if announcement.created_at != current_user.id:
        raise ForbiddenException("You do not own this announcement to modify it")

    return announcement
