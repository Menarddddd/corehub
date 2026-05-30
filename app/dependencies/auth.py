from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.refresh_token import RefreshRepository
from app.repositories.user import UserRepository
from app.services.auth import AuthService


def get_auth_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AuthService:
    user_repo = UserRepository(db)
    refresh_repo = RefreshRepository(db)
    return AuthService(user_repo, refresh_repo)
