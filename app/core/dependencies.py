from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import User
from app.repositories.users import UserRepository
from app.schemas.enums import Role
from app.services.users import UserService


def required_roles(*roles: Role):
    def role_checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the permission to perform this action",
            )
        return current_user

    return role_checker


def get_user_service(db: Annotated[AsyncSession, Depends(get_db)]) -> UserService:
    """Wires DB to repo and pass repo to service"""
    repo = UserRepository(db)
    return UserService(repo)
