from datetime import datetime, timezone
from uuid import UUID

from app.core.exceptions import BadRequestException, FieldNotFoundException
from app.models.announcements import Announcement
from app.models.users import User
from app.repositories.announcement import AnnouncementRepository
from app.schemas.announcement import (
    AnnouncementCreate,
    AnnouncementPageResponse,
    AnnouncementResponse,
    AnnouncementUpdate,
)
from app.schemas.cursor import CursorPageInfo
from app.schemas.enum import AnnouncementPriority, AnnouncementStatus
from app.utils.cursor import get_cursor_info


class AnnouncementService:
    def __init__(self, repo: AnnouncementRepository):
        self.repo = repo

    def _build_common_conditions(
        self, status: AnnouncementStatus | None, priority: AnnouncementPriority | None
    ) -> list:
        conditions = []

        if status is not None:
            conditions.append(
                Announcement.expires_at < datetime.now(timezone.utc)
                if status.value == AnnouncementStatus.EXPIRED.value
                else Announcement.expires_at > datetime.now(timezone.utc)
            )

        if priority is not None:
            conditions.append(Announcement.priority == priority.value)

        return conditions

    async def get_announcements_service(
        self,
        user_id: UUID | None,
        status: AnnouncementStatus | None,
        priority: AnnouncementPriority | None,
        limit: int,
        cursor: str | None,
    ) -> AnnouncementPageResponse:
        """
        Fetch all announcements with cursor-based pagination.
        Can also fetch specific user created announcements,
        Returns announcements ordered by created_at descending
        so the newest announcements appear first.
        """
        conditions = self._build_common_conditions(status=status, priority=priority)

        if user_id is not None:
            conditions.append(Announcement.user_id == user_id)

        announcements = await self.repo.get_announcements(
            *conditions, limit=limit, cursor=cursor
        )
        announcements, has_next, next_cursor = get_cursor_info(announcements, limit)

        return AnnouncementPageResponse(
            items=[
                AnnouncementResponse.model_validate(announcement)
                for announcement in announcements
            ],
            page_info=CursorPageInfo(has_next=has_next, next_cursor=next_cursor),
        )

    async def get_announcement_service(self, announcement_id: UUID) -> Announcement:
        """
        Fetch a single announcement by its ID.
        Raises 404 if the announcement does not exist.
        """
        announcement = await self.repo.get_by_id(announcement_id)
        if not announcement:
            raise FieldNotFoundException("announcements", str(announcement_id))
        return announcement

    async def create_announcement_service(
        self, form_data: AnnouncementCreate, current_user: User
    ) -> Announcement:
        """
        Create a new announcement authored by the current user.
        The user_id is automatically set from the authenticated user.
        Raises 400 if the announcement could not be saved.
        """
        try:
            new_announcement = Announcement(
                user_id=current_user.id,
                title=form_data.title,
                body=form_data.body,
                priority=form_data.priority,
            )
            return await self.repo.save(new_announcement)
        except Exception:
            raise BadRequestException("Could not create announcement")

    async def update_announcement_service(
        self,
        announcement_id: UUID,
        form_data: AnnouncementUpdate,
    ) -> Announcement:
        """
        Update the details of an existing announcement.
        Uses exclude_unset=True so only fields included
        in the request body are updated.
        Raises 404 if the announcement does not exist.
        Raises 400 if no fields are provided in the request body.
        """
        announcement_data = form_data.model_dump(exclude_unset=True)
        if not announcement_data:
            raise BadRequestException("No fields to update")

        announcement = await self.repo.get_by_id(announcement_id)
        if not announcement:
            raise FieldNotFoundException("announcements", str(announcement_id))

        for key, val in announcement_data.items():
            setattr(announcement, key, val)

        try:
            return await self.repo.update(announcement)
        except Exception:
            raise BadRequestException("Could not update announcement")

    async def delete_announcement_service(self, announcement_id: UUID) -> None:
        """
        Hard delete an announcement by its ID.
        This action is permanent and cannot be undone.
        Raises 404 if the announcement does not exist.
        """
        announcement = await self.repo.get_by_id(announcement_id)
        if not announcement:
            raise FieldNotFoundException("announcements", str(announcement_id))
        await self.repo.delete(announcement)
