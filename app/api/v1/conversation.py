from typing import Annotated
from uuid import UUID
from fastapi import Query, status
from fastapi.routing import APIRouter

from app.dependencies.conversation import ConversationServiceDep

from app.dependencies.user import AnyAuthenticated
from app.schemas.conversation import (
    ConversationInboxResponse,
    ConversationResponse,
    CreateDMRequest,
    CreateGroupRequest,
    AddMemberRequest,
    MessageResponse,
    UpdateGroupRequest,
    MessagePageResponse,
    SendMessageRequest,
)

router = APIRouter()


# Inbox
@router.get(
    "",
    response_model=ConversationInboxResponse,
    status_code=status.HTTP_200_OK,
)
async def get_inbox(
    service: ConversationServiceDep,
    current_user: AnyAuthenticated,
    limit: Annotated[int, Query(ge=1, lt=50)] = 10,
    cursor: Annotated[str | None, Query()] = None,
):
    """
    Retrieve the current user's inbox.
    Shows all conversations with last message preview
    and unread count per conversation.
    Ordered by most recent message first.
    Accessible by all authenticated roles.
    """
    return await service.get_inbox_service(current_user.id, limit, cursor)


# Create Conversation
@router.post(
    "/dm",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_dm(
    form_data: CreateDMRequest,
    service: ConversationServiceDep,
    current_user: AnyAuthenticated,
):
    """
    Create a direct message conversation with another user.
    If a DM already exists between the two users,
    returns the existing conversation instead of creating a new one.
    Cannot create a DM with yourself.
    Accessible by all authenticated roles.
    """
    return await service.create_dm_service(current_user, form_data.user_id)


@router.post(
    "/group",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_group(
    form_data: CreateGroupRequest,
    service: ConversationServiceDep,
    current_user: AnyAuthenticated,
):
    """
    Create a group conversation with multiple users.
    The creator is automatically added as a group admin.
    Requires at least one other member besides the creator.
    Accessible by all authenticated roles.
    """
    return await service.create_group_service(current_user, form_data)


# Conversation Actions
@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
)
async def get_conversation(
    conversation_id: UUID,
    service: ConversationServiceDep,
    current_user: AnyAuthenticated,
):
    """
    Retrieve details of a specific conversation.
    Raises 403 if the current user is not a member.
    Raises 404 if the conversation does not exist.
    Accessible by all authenticated roles.
    """
    return await service.get_conversation_service(conversation_id, current_user)


@router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
)
async def update_group(
    conversation_id: UUID,
    form_data: UpdateGroupRequest,
    service: ConversationServiceDep,
    current_user: AnyAuthenticated,
):
    """
    Update a group conversation name.
    Only group admins can update the group name.
    Cannot update DM conversations.
    Raises 403 if the current user is not a group admin.
    Accessible by all authenticated roles.
    """
    return await service.update_group_service(conversation_id, form_data, current_user)


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def leave_conversation(
    conversation_id: UUID,
    service: ConversationServiceDep,
    current_user: AnyAuthenticated,
):
    """
    Leave a conversation.
    For DMs: both users are removed and conversation is deleted.
    For Groups: only the current user leaves.
    If the last admin leaves a group, the longest member becomes admin.
    Accessible by all authenticated roles.
    """
    await service.leave_conversation_service(conversation_id, current_user)


# Members
@router.post(
    "/{conversation_id}/members",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    conversation_id: UUID,
    form_data: AddMemberRequest,
    service: ConversationServiceDep,
    current_user: AnyAuthenticated,
):
    """
    Add a new member to a group conversation.
    Only group admins can add members.
    Cannot add members to DM conversations.
    Raises 409 if the user is already a member.
    Accessible by all authenticated roles.
    """
    return await service.add_member_service(
        conversation_id, form_data.user_id, current_user
    )


@router.delete(
    "/{conversation_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_member(
    conversation_id: UUID,
    user_id: UUID,
    service: ConversationServiceDep,
    current_user: AnyAuthenticated,
):
    """
    Remove a member from a group conversation.
    Only group admins can remove members.
    Cannot remove members from DM conversations.
    Cannot remove the last admin from a group.
    Accessible by all authenticated roles.
    """
    await service.remove_member_service(conversation_id, user_id, current_user)


# Messages
@router.get(
    "/{conversation_id}/messages",
    response_model=MessagePageResponse,
    status_code=status.HTTP_200_OK,
)
async def get_messages(
    conversation_id: UUID,
    service: ConversationServiceDep,
    current_user: AnyAuthenticated,
    limit: Annotated[int, Query(ge=1, lt=50)] = 20,
    cursor: Annotated[str | None, Query()] = None,
):
    """
    Retrieve paginated messages in a conversation.
    Ordered by sent_at ascending (oldest first like a real chat).
    Raises 403 if the current user is not a member.
    Accessible by all authenticated roles.
    """
    return await service.get_messages_service(
        conversation_id, current_user, limit, cursor
    )


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    conversation_id: UUID,
    form_data: SendMessageRequest,
    service: ConversationServiceDep,
    current_user: AnyAuthenticated,
):
    """
    Send a message to a conversation.
    Raises 403 if the current user is not a member.
    Accessible by all authenticated roles.
    """
    return await service.send_message_service(
        conversation_id, form_data.content, current_user
    )


@router.delete(
    "/{conversation_id}/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_message(
    conversation_id: UUID,
    message_id: UUID,
    service: ConversationServiceDep,
    current_user: AnyAuthenticated,
):
    """
    Delete a specific message from a conversation.
    Only the message sender can delete their own message.
    Raises 403 if the current user is not the message sender.
    Accessible by all authenticated roles.
    """
    await service.delete_message_service(conversation_id, message_id, current_user)


@router.patch(
    "/{conversation_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def mark_conversation_as_read(
    conversation_id: UUID,
    service: ConversationServiceDep,
    current_user: AnyAuthenticated,
):
    """
    Mark all messages in a conversation as read.
    Only marks messages not sent by the current user.
    Accessible by all authenticated roles.
    """
    await service.mark_as_read_service(conversation_id, current_user)
