import redis.asyncio as aioredis
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis
from app.core.security import get_current_user
from app.models.users import User
from app.repositories.user import UserRepository
from app.schemas.enum import Role
from app.services.user import UserService


def get_user_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
) -> UserService:
    repo = UserRepository(db)
    return UserService(repo, redis)


def required_roles(*roles: Role):
    def role_checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the permission to perform this action",
            )
        return current_user

    return role_checker
