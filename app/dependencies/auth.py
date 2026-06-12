from typing import Annotated
from fastapi import Depends

from app.core.database import AsyncDB
from app.repositories.refresh_token import RefreshRepository
from app.repositories.user import UserRepository
from app.services.auth import AuthService


def get_auth_service(db: AsyncDB) -> AuthService:
    user_repo = UserRepository(db)
    refresh_repo = RefreshRepository(db)
    return AuthService(user_repo, refresh_repo)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
