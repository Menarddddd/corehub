from uuid import UUID
from typing import Sequence
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversations import Conversation
from app.models.conversation_members import ConversationMember
from app.models.messages import Message
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Conversation)

    async def get_member(
        self, conversation_id: UUID, user_id: UUID
    ) -> ConversationMember | None:
        """
        Check if a user is a member of a conversation.
        Returns the member object or None if not a member.
        """
        stmt = select(ConversationMember).where(
            ConversationMember.conversation_id == conversation_id,
            ConversationMember.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_members(
        self, conversation_id: UUID
    ) -> Sequence[ConversationMember]:
        """Get all members of a conversation."""
        stmt = select(ConversationMember).where(
            ConversationMember.conversation_id == conversation_id
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_existing_dm(self, user_a: UUID, user_b: UUID) -> Conversation | None:
        """
        Check if a DM conversation already exists between two users.
        Prevents creating duplicate DMs between the same two people.
        """
        stmt = (
            select(Conversation)
            .join(
                ConversationMember,
                ConversationMember.conversation_id == Conversation.id,
            )
            .where(
                Conversation.is_group == False,
                ConversationMember.user_id.in_([user_a, user_b]),
            )
            .group_by(Conversation.id)
            .having(func.count(ConversationMember.user_id) == 2)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_inbox(
        self,
        user_id: UUID,
        limit: int,
        cursor: str | None = None,
    ) -> Sequence:
        """
        Get all conversations for a user with last message info.
        Ordered by most recent message first.
        Returns raw rows with conversation_id, last_message, last_message_at.
        """
        last_message_subq = (
            select(
                Message.conversation_id,
                func.max(Message.sent_at).label("last_message_at"),
            )
            .group_by(Message.conversation_id)
            .subquery()  # returns a table
        )

        stmt = (
            select(
                Conversation.id.label("conversation_id"),
                Conversation.name,
                Conversation.is_group,
                last_message_subq.c.last_message_at,
            )
            .join(
                ConversationMember,
                ConversationMember.conversation_id == Conversation.id,
            )
            .outerjoin(
                last_message_subq,
                last_message_subq.c.conversation_id == Conversation.id,
            )
            .where(ConversationMember.user_id == user_id)
            .order_by(last_message_subq.c.last_message_at.desc())
            .limit(limit + 1)
        )

        result = await self.db.execute(stmt)
        return result.all()

    async def get_unread_count(self, conversation_id: UUID, user_id: UUID) -> int:
        """
        Count unread messages in a conversation for a specific user.
        Only counts messages not sent by the user themselves.
        """
        stmt = select(func.count(Message.id)).where(
            Message.conversation_id == conversation_id,
            Message.sender_id != user_id,
            Message.sent_at  # sent after joined
            > select(
                func.coalesce(
                    ConversationMember.joined_at,
                    datetime.min,
                )
            )
            .where(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.user_id == user_id,
            )
            .scalar_subquery(),  # returns one val
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def get_messages(
        self,
        conversation_id: UUID,
        limit: int,
        cursor: str | None = None,
    ) -> Sequence[Message]:
        """
        Fetch messages in a conversation with cursor-based pagination.
        Ordered by sent_at ascending (oldest first like a real chat).
        """
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sent_at.asc(), Message.id.asc())
            .limit(limit + 1)
        )

        if cursor:
            from app.utils.cursor import decode_cursor

            decoded = decode_cursor(cursor)
            stmt = stmt.where(Message.sent_at > decoded.created_at)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_last_message(self, conversation_id: UUID) -> Message | None:
        """
        Get the most recent message in a conversation.
        Used for inbox preview.
        """
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sent_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def add_member(
        self, conversation_id: UUID, user_id: UUID, is_admin: bool = False
    ) -> ConversationMember:
        """
        Add a user to a conversation.
        Raises IntegrityError if user is already a member.
        """
        member = ConversationMember(
            conversation_id=conversation_id,
            user_id=user_id,
            is_admin=is_admin,
        )
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def remove_member(self, member: ConversationMember) -> None:
        """Remove a member from a conversation."""
        await self.db.delete(member)
        await self.db.commit()

    async def save_message(self, message: Message) -> Message:
        """Save a new message to the database."""
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def delete_message(self, message: Message) -> None:
        """Delete a specific message."""
        await self.db.delete(message)
        await self.db.commit()

    async def get_message(self, message_id: UUID) -> Message | None:
        """Get a single message by its ID."""
        stmt = select(Message).where(Message.id == message_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
