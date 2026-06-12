from typing import Annotated
from uuid import UUID

from fastapi import Depends

from app.core.database import AsyncDB
from app.core.exceptions import FieldNotFoundException, ForbiddenException
from app.core.redis import ARedis
from app.core.security import GetCurrentUser
from app.models.notifications import Notification
from app.repositories.notification import NotificationRepository
from app.services.notification import NotificationService


def get_notification_service(
    db: AsyncDB,
    redis: ARedis,
    user: GetCurrentUser,
) -> NotificationService:
    """Wire DepartmentRepository and UserRepository into DepartmentService."""
    repo = NotificationRepository(db)
    return NotificationService(repo, redis)


async def check_notification_owner(
    notification_id: UUID,
    current_user: GetCurrentUser,
    db: AsyncDB,
) -> Notification:
    repo = NotificationRepository(db)

    notification = await repo.get_by_id(notification_id)

    if not notification:
        raise FieldNotFoundException("notifications", str(notification_id))

    if notification.user_id != current_user.id:
        raise ForbiddenException("You do not own this notification to access/modify it")

    return notification


NotificationServiceDep = Annotated[
    NotificationService, Depends(get_notification_service)
]
CheckNotificationOwner = Annotated[Notification, Depends(check_notification_owner)]
