from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import FieldNotFoundException, ForbiddenException
from app.core.security import get_current_user
from app.models.notifications import Notification
from app.models.users import User
from app.repositories.department import DepartmentRepository
from app.repositories.notification import NotificationRepository
from app.repositories.user import UserRepository
from app.services.department import DepartmentService


def get_notification_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DepartmentService:
    """Wire DepartmentRepository and UserRepository into DepartmentService."""
    repo = DepartmentRepository(db)
    user_repo = UserRepository(db)
    return DepartmentService(repo, user_repo)


async def check_notification_owner(
    notification_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Notification:
    repo = NotificationRepository(db)

    notification = await repo.get_by_id(notification_id)

    if not notification:
        raise FieldNotFoundException("notifications", str(notification_id))

    if notification.user_id != current_user.id:
        raise ForbiddenException("You do not own this notification to access/modify it")

    return notification
