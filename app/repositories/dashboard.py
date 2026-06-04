from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models.tasks import Task
from app.models.notifications import Notification
from app.models.conversation_members import ConversationMember
from app.models.messages import Message
from app.models.announcements import Announcement


class DashboardRepository:
    def __init__(self, session_factory: async_sessionmaker):
        self.session_factory = session_factory

    async def get_task_counts(self, user_id: UUID) -> dict:
        """Count tasks by status assigned to a user."""
        async with self.session_factory() as db:
            result = await db.execute(
                select(
                    func.count(Task.id).label("total"),
                    func.count(Task.id).filter(
                        Task.status == "pending"
                    ).label("pending"),
                    func.count(Task.id).filter(
                        Task.status == "in_progress"
                    ).label("in_progress"),
                    func.count(Task.id).filter(
                        Task.status == "completed"
                    ).label("completed"),
                    func.count(Task.id).filter(
                        Task.status == "cancelled"
                    ).label("cancelled"),
                ).where(Task.assigned_to_id == user_id)
            )

            row = result.one()

            return {
                "total": row.total,
                "pending": row.pending,
                "in_progress": row.in_progress,
                "completed": row.completed,
                "cancelled": row.cancelled,
            }

    async def get_unread_notification_count(self, user_id: UUID) -> int:
        """Count unread notifications for a user."""
        async with self.session_factory() as db:
            result = await db.execute(
                select(func.count(Notification.id)).where(
                    Notification.user_id == user_id,
                    Notification.read_at.is_(None),
                )
            )

            return result.scalar() or 0

    async def get_unread_message_count(self, user_id: UUID) -> int:
        """
        Count unread messages across all conversations
        the user is a member of.
        """
        async with self.session_factory() as db:
            member_subquery = (
                select(ConversationMember.conversation_id)
                .where(ConversationMember.user_id == user_id)
                .subquery()
            )

            result = await db.execute(
                select(func.count(Message.id)).where(
                    Message.conversation_id.in_(select(member_subquery)),
                    Message.sender_id != user_id,
                )
            )

            return result.scalar() or 0


    async def get_recent_announcements(self, limit: int = 5):
        """Get the most recent announcements that have not expired."""
        async with self.session_factory() as db:
            result = await db.execute(
                select(Announcement)
                .where(Announcement.expires_at > datetime.now(timezone.utc))
                .order_by(Announcement.created_at.desc())
                .limit(limit)
            )

            return result.scalars().all()