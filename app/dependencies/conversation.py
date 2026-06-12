from typing import Annotated
from fastapi import Depends

from app.core.database import AsyncDB
from app.core.security import GetCurrentUser
from app.repositories.conversation import ConversationRepository
from app.repositories.notification import NotificationRepository
from app.repositories.user import UserRepository
from app.services.conversation import ConversationService


def get_conversation_service(
    db: AsyncDB,
    current_user: GetCurrentUser,
) -> ConversationService:
    """Wire ConversationRepository into ConversationService."""
    repo = ConversationRepository(db)
    user_repo = UserRepository(db)
    notif_repo = NotificationRepository(db)
    return ConversationService(repo, user_repo, notif_repo)


ConversationServiceDep = Annotated[
    ConversationService, Depends(get_conversation_service)
]
