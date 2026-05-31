from typing import Annotated
from uuid import UUID
from fastapi import Depends, Query, status
from fastapi.routing import APIRouter

from app.core.security import get_current_user
from app.dependencies.announcement import get_announcement_service
from app.dependencies.user import required_roles
from app.models.users import User
from app.schemas.announcement import (
    AnnouncementCreate,
    AnnouncementPageResponse,
    AnnouncementResponse,
    AnnouncementUpdate,
)
from app.schemas.enum import AnnouncementPriority, AnnouncementStatus, Role
from app.services.announcement import AnnouncementService

router = APIRouter()


@router.get("", response_model=AnnouncementPageResponse, status_code=status.HTTP_200_OK)
async def get_announcements(
    service: Annotated[AnnouncementService, Depends(get_announcement_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    user_id: UUID | None = None,
    status: AnnouncementStatus | None = None,
    priority: AnnouncementPriority | None = None,
    limit: Annotated[int, Query(ge=1, lt=50)] = 10,
    cursor: Annotated[str | None, Query()] = None,
):
    """
    Retrieve a paginated list of all announcements.
    Can also retrieve all of the created announcements of a user,
    Supports cursor-based pagination.
    Accessible by all authenticated roles.
    """
    return await service.get_announcements_service(
        user_id=user_id,
        status=status,
        priority=priority,
        limit=limit,
        cursor=cursor,
    )


@router.post(
    "", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED
)
async def create_announcement(
    form_data: AnnouncementCreate,
    service: Annotated[AnnouncementService, Depends(get_announcement_service)],
    current_user: Annotated[User, Depends(required_roles(Role.ADMIN))],
):
    """
    Create a new announcement.
    The current user is automatically set as the announcement author.
    Restricted to ADMIN role only.
    """
    return await service.create_announcement_service(form_data, current_user)


@router.get(
    "/{announcement_id}",
    response_model=AnnouncementResponse,
    status_code=status.HTTP_200_OK,
)
async def get_announcement(
    announcement_id: UUID,
    service: Annotated[AnnouncementService, Depends(get_announcement_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Retrieve a single announcement by its ID.
    Raises 404 if the announcement does not exist.
    Accessible by all authenticated roles.
    """
    return await service.get_announcement_service(announcement_id)


@router.patch(
    "/{announcement_id}",
    response_model=AnnouncementResponse,
    status_code=status.HTTP_200_OK,
)
async def update_announcement(
    announcement_id: UUID,
    form_data: AnnouncementUpdate,
    service: Annotated[AnnouncementService, Depends(get_announcement_service)],
    current_user: Annotated[User, Depends(required_roles(Role.ADMIN))],
):
    """
    Update the details of an existing announcement.
    Only fields included in the request body will be updated.
    Raises 404 if the announcement does not exist.
    Raises 400 if no fields are provided.
    Restricted to ADMIN role only.
    """
    return await service.update_announcement_service(announcement_id, form_data)


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_announcement(
    announcement_id: UUID,
    service: Annotated[AnnouncementService, Depends(get_announcement_service)],
    current_user: Annotated[User, Depends(required_roles(Role.ADMIN))],
):
    """
    Delete an announcement by its ID.
    This action is permanent and cannot be undone.
    Raises 404 if the announcement does not exist.
    Restricted to ADMIN role only.
    """
    return await service.delete_announcement_service(announcement_id)
