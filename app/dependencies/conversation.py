from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.conversation import ConversationRepository
from app.repositories.user import UserRepository
from app.services.conversation import ConversationService


def get_conversation_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConversationService:
    """Wire ConversationRepository into ConversationService."""
    repo = ConversationRepository(db)
    user_repo = UserRepository(db)
    return ConversationService(repo, user_repo)
