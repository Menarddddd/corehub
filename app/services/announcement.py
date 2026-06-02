import redis.asyncio as aioredis
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
    def __init__(self, repo: AnnouncementRepository, redis: aioredis.Redis):
        self.repo = repo
        self.redis = redis

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

    async def _build_cache_key(
        self,
        user_id: UUID | None,
        status: AnnouncementStatus | None,
        priority: AnnouncementPriority | None,
        limit: int,
        cursor: str | None,
    ) -> str:
        u = user_id if user_id else "none"
        s = status if status else "none"
        p = priority if priority else "none"
        c = cursor if cursor else "none"

        return f"announcement:user:{u}:status:{s}:priority:{p}:cursor:{c}"

    async def _invalidate_announcements_cache(self) -> None:
        "Delete ALL cached user list keys"
        async for key in self.redis.scan_iter(match="announcement:*"):
            await self.redis.delete(key)

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
        cache_key = await self._build_cache_key(
            user_id, status, priority, limit, cursor
        )
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            return AnnouncementPageResponse.model_validate_json(cached_data)

        conditions = self._build_common_conditions(status=status, priority=priority)

        if user_id is not None:
            conditions.append(Announcement.user_id == user_id)

        announcements = await self.repo.get_announcements(
            *conditions, limit=limit, cursor=cursor
        )
        announcements, has_next, next_cursor = get_cursor_info(announcements, limit)

        response = AnnouncementPageResponse(
            items=[
                AnnouncementResponse.model_validate(announcement)
                for announcement in announcements
            ],
            page_info=CursorPageInfo(has_next=has_next, next_cursor=next_cursor),
        )

        await self.redis.set(
            cache_key,
            response.model_dump_json(),
            ex=1800,
        )

        return response

    async def get_announcement_service(
        self, announcement_id: UUID
    ) -> AnnouncementResponse:
        """
        Fetch a single announcement by its ID.
        Raises 404 if the announcement does not exist.
        """
        cache_key = f"announcement:{announcement_id}"
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            return AnnouncementResponse.model_validate_json(cached_data)

        announcement = await self.repo.get_by_id(announcement_id)
        if not announcement:
            raise FieldNotFoundException("announcements", str(announcement_id))

        response = AnnouncementResponse.model_validate(announcement)

        await self.redis.set(
            cache_key,
            response.model_dump_json(),
            ex=1800,
        )

        return response

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
            response = await self.repo.save(new_announcement)
            await self._invalidate_announcements_cache()
            return response
        except Exception:
            raise BadRequestException("Could not create announcement")

    async def update_announcement_service(
        self,
        announcement: Announcement,
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

        for key, val in announcement_data.items():
            setattr(announcement, key, val)

        try:
            response = await self.repo.update(announcement)
            await self._invalidate_announcements_cache()
            return response
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
        await self._invalidate_announcements_cache()
