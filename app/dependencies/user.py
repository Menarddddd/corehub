from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.core.database import AsyncDB
from app.core.redis import ARedis
from app.core.security import GetCurrentUser, get_current_user
from app.models.users import User
from app.repositories.user import UserRepository
from app.schemas.enum import Role
from app.services.user import UserService


def get_user_service(
    db: AsyncDB,
    redis: ARedis,
    current_user: GetCurrentUser,
) -> UserService:
    repo = UserRepository(db)
    return UserService(repo, redis)


def required_roles(*roles: Role):
    def role_checker(current_user: GetCurrentUser) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the permission to perform this action",
            )
        return current_user

    return role_checker


UserServiceDep = Annotated[UserService, Depends(get_user_service)]

# This dependencies are only use in APIs for RBAC feature
AdminOnly = Annotated[User, Depends(required_roles(Role.ADMIN))]
AdminOrManager = Annotated[User, Depends(required_roles(Role.ADMIN, Role.MANAGER))]
AnyAuthenticated = Annotated[User, Depends(get_current_user)]
