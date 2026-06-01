from uuid import UUID
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    BadRequestException,
    DuplicateEntryException,
    FieldNotFoundException,
    ForbiddenException,
)
from app.models.conversations import Conversation
from app.models.messages import Message
from app.models.users import User
from app.repositories.conversation import ConversationRepository
from app.repositories.user import UserRepository
from app.schemas.conversation import (
    ConversationInboxItem,
    ConversationInboxResponse,
    CreateGroupRequest,
    MessagePageResponse,
    MessageResponse,
    UpdateGroupRequest,
)
from app.schemas.cursor import CursorPageInfo
from app.utils.cursor import encode_cursor, get_cursor_info, CursorPayload


class ConversationService:
    def __init__(self, repo: ConversationRepository, user_repo: UserRepository):
        self.repo = repo
        self.user_repo = user_repo

    async def get_inbox_service(
        self, user_id: UUID, limit: int, cursor: str | None
    ) -> ConversationInboxResponse:
        """
        Fetch the user's inbox showing all conversations
        with last message preview and unread count.
        """
        rows = await self.repo.get_inbox(user_id, limit, cursor)

        has_next = len(rows) > limit
        if has_next:
            rows = rows[:limit]

        items = []
        for row in rows:
            last_message = await self.repo.get_last_message(row.conversation_id)
            unread_count = await self.repo.get_unread_count(
                row.conversation_id, user_id
            )
            items.append(
                ConversationInboxItem(
                    conversation_id=row.conversation_id,
                    name=row.name,
                    is_group=row.is_group,
                    last_message=last_message.content if last_message else None,
                    last_message_at=row.last_message_at,
                    unread_count=unread_count,
                )
            )

        next_cursor = None
        if has_next and rows:
            last = rows[-1]
            next_cursor = encode_cursor(
                CursorPayload(
                    item_id=last.conversation_id,
                    created_at=last.last_message_at,
                )
            )

        return ConversationInboxResponse(
            items=items,
            page_info=CursorPageInfo(has_next=has_next, next_cursor=next_cursor),
        )

    async def create_dm_service(
        self, current_user: User, other_user_id: UUID
    ) -> Conversation:
        """
        Create a DM conversation between two users.
        If a DM already exists, return the existing one.
        Prevents creating a DM with yourself.
        """
        user = await self.user_repo.get_by_id(other_user_id)
        if not user:
            raise FieldNotFoundException("users", str(other_user_id))

        if current_user.id == other_user_id:
            raise BadRequestException("You cannot create a DM with yourself")

        # Check if DM already exists
        existing = await self.repo.get_existing_dm(current_user.id, other_user_id)
        if existing:
            return existing

        # Create new DM conversation
        conversation = Conversation(
            is_group=False,
            created_by_id=current_user.id,
        )
        await self.repo.save(conversation)

        # Add both users as members
        await self.repo.add_member(conversation.id, current_user.id)
        await self.repo.add_member(conversation.id, other_user_id)

        return conversation

    async def create_group_service(
        self, current_user: User, form_data: CreateGroupRequest
    ) -> Conversation:
        """
        Create a group conversation.
        Creator is automatically added as group admin.
        All provided member_ids are added as regular members.
        Prevents adding the creator twice.
        """
        # Prevent creator from adding themselves
        member_ids = [uid for uid in form_data.member_ids if uid != current_user.id]

        conversation = Conversation(
            name=form_data.name,
            is_group=True,
            created_by_id=current_user.id,
        )
        await self.repo.save(conversation)

        # Creator is admin
        await self.repo.add_member(conversation.id, current_user.id, is_admin=True)

        # Add all other members
        for user_id in member_ids:
            await self.repo.add_member(conversation.id, user_id)

        return conversation

    async def get_conversation_service(
        self, conversation_id: UUID, current_user: User
    ) -> Conversation:
        """
        Fetch a single conversation.
        Raises 404 if not found.
        Raises 403 if current user is not a member.
        """
        conversation = await self.repo.get_by_id(conversation_id)
        if not conversation:
            raise FieldNotFoundException("conversations", str(conversation_id))

        member = await self.repo.get_member(conversation_id, current_user.id)
        if not member:
            raise ForbiddenException("You are not a member of this conversation")

        return conversation

    async def update_group_service(
        self,
        conversation_id: UUID,
        form_data: UpdateGroupRequest,
        current_user: User,
    ) -> Conversation:
        """
        Update a group name.
        Only group admins can update.
        Cannot update DM conversations.
        """
        conversation = await self.get_conversation_service(
            conversation_id, current_user
        )

        if not conversation.is_group:
            raise BadRequestException("Cannot update a DM conversation")

        member = await self.repo.get_member(conversation_id, current_user.id)
        if not member or not member.is_admin:
            raise ForbiddenException("Only group admins can update the group")

        update_data = form_data.model_dump(exclude_unset=True)
        if not update_data:
            raise BadRequestException("No fields to update")

        for key, val in update_data.items():
            setattr(conversation, key, val)

        return await self.repo.update(conversation)

    async def leave_conversation_service(
        self, conversation_id: UUID, current_user: User
    ) -> None:
        """
        Leave a conversation.
        For DMs: deletes the entire conversation.
        For Groups: removes only the current user.
        """
        conversation = await self.get_conversation_service(
            conversation_id, current_user
        )

        member = await self.repo.get_member(conversation_id, current_user.id)
        if not member:
            raise ForbiddenException("You are not a member of this conversation")

        if not conversation.is_group:
            # Delete the entire DM conversation
            await self.repo.delete(conversation)
        else:
            # Just remove this user from the group
            await self.repo.remove_member(member)

    async def add_member_service(
        self,
        conversation_id: UUID,
        user_id: UUID,
        current_user: User,
    ) -> Conversation:
        """
        Add a member to a group conversation.
        Only group admins can add members.
        Cannot add to DM conversations.
        Raises 409 if already a member.
        """
        conversation = await self.get_conversation_service(
            conversation_id, current_user
        )

        if not conversation.is_group:
            raise BadRequestException("Cannot add members to a DM conversation")

        member = await self.repo.get_member(conversation_id, current_user.id)
        if not member or not member.is_admin:
            raise ForbiddenException("Only group admins can add members")

        try:
            await self.repo.add_member(conversation_id, user_id)
        except IntegrityError:
            raise DuplicateEntryException("members", str(user_id))

        return conversation

    async def remove_member_service(
        self,
        conversation_id: UUID,
        user_id: UUID,
        current_user: User,
    ) -> None:
        """
        Remove a member from a group conversation.
        Only group admins can remove members.
        Cannot remove from DM conversations.
        """
        conversation = await self.get_conversation_service(
            conversation_id, current_user
        )

        if not conversation.is_group:
            raise BadRequestException("Cannot remove members from a DM conversation")

        admin_member = await self.repo.get_member(conversation_id, current_user.id)
        if not admin_member or not admin_member.is_admin:
            raise ForbiddenException("Only group admins can remove members")

        target_member = await self.repo.get_member(conversation_id, user_id)
        if not target_member:
            raise FieldNotFoundException("members", str(user_id))

        await self.repo.remove_member(target_member)

    async def get_messages_service(
        self,
        conversation_id: UUID,
        current_user: User,
        limit: int,
        cursor: str | None,
    ) -> MessagePageResponse:
        """
        Fetch paginated messages in a conversation.
        Raises 403 if current user is not a member.
        """
        conversation = await self.get_conversation_service(
            conversation_id, current_user
        )

        messages = await self.repo.get_messages(conversation_id, limit, cursor)
        messages, has_next, next_cursor = get_cursor_info(messages, limit)

        return MessagePageResponse(
            items=[MessageResponse.model_validate(m) for m in messages],
            page_info=CursorPageInfo(has_next=has_next, next_cursor=next_cursor),
        )

    async def send_message_service(
        self,
        conversation_id: UUID,
        content: str,
        current_user: User,
    ) -> Message:
        """
        Send a message to a conversation.
        Raises 403 if current user is not a member.
        """
        await self.get_conversation_service(conversation_id, current_user)

        message = Message(
            conversation_id=conversation_id,
            sender_id=current_user.id,
            content=content,
        )
        return await self.repo.save_message(message)

    async def delete_message_service(
        self,
        conversation_id: UUID,
        message_id: UUID,
        current_user: User,
    ) -> None:
        """
        Delete a message.
        Only the sender can delete their own message.
        Raises 404 if message not found.
        Raises 403 if not the sender.
        """
        await self.get_conversation_service(conversation_id, current_user)

        message = await self.repo.get_message(message_id)
        if not message:
            raise FieldNotFoundException("messages", str(message_id))

        if message.sender_id != current_user.id:
            raise ForbiddenException("You can only delete your own messages")

        await self.repo.delete_message(message)

    async def mark_as_read_service(
        self, conversation_id: UUID, current_user: User
    ) -> None:
        """
        Mark all messages in a conversation as read.
        This would update a read_receipts table in a more
        advanced implementation. For now this is a placeholder.
        """
        await self.get_conversation_service(conversation_id, current_user)
        # Implementation depends on your read tracking strategy
