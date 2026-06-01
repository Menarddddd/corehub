from typing import Annotated
from fastapi import Depends, Query, status
from fastapi.routing import APIRouter

from app.core.security import get_current_user
from app.dependencies.notification import (
    check_notification_owner,
    get_notification_service,
)
from app.models.notifications import Notification
from app.models.users import User
from app.schemas.notification import NotificationPageResponse, NotificationResponse
from app.services.notification import NotificationService

router = APIRouter()


@router.get("", response_model=NotificationPageResponse, status_code=status.HTTP_200_OK)
async def get_notifications(
    service: Annotated[NotificationService, Depends(get_notification_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: Annotated[int, Query(ge=1, lt=50)] = 10,
    cursor: Annotated[str | None, Query()] = None,
):
    """
    Retrieve paginated notifications for the current user.
    Accessible by all authenticated roles.
    """
    return await service.get_notifications_service(current_user.id, limit, cursor)


@router.get(
    "/unread",
    response_model=NotificationPageResponse,
    status_code=status.HTTP_200_OK,
)
async def get_unread_notifications(
    service: Annotated[NotificationService, Depends(get_notification_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: Annotated[int, Query(ge=1, lt=50)] = 10,
    cursor: Annotated[str | None, Query()] = None,
):
    """
    Retrieve only unread notifications for the current user.
    Accessible by all authenticated roles.
    """
    return await service.get_unread_notifications_service(
        current_user.id, limit, cursor
    )


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
)
async def mark_as_read(
    notification: Annotated[Notification, Depends(check_notification_owner)],
    service: Annotated[NotificationService, Depends(get_notification_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Mark a single notification as read.
    Sets the read_at timestamp to now.
    Accessible by all authenticated roles.
    """
    return await service.mark_as_read_service(notification)


@router.patch(
    "/read-all",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def mark_all_as_read(
    service: Annotated[NotificationService, Depends(get_notification_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Mark all notifications as read for the current user.
    Accessible by all authenticated roles.
    """
    await service.mark_all_as_read_service(current_user.id)


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_notification(
    notification: Annotated[Notification, Depends(check_notification_owner)],
    service: Annotated[NotificationService, Depends(get_notification_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Delete a single notification.
    Users can only delete their own notifications.
    Accessible by all authenticated roles.
    """
    await service.delete_notification_service(notification)
