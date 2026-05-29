from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import User
from app.repositories.department import DepartmentRepository
from app.repositories.user import UserRepository
from app.repositories.refresh_token import RefreshRepository
from app.schemas.enum import Role
from app.services.auth import AuthService
from app.services.department import DepartmentService
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


def get_auth_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AuthService:
    user_repo = UserRepository(db)
    refresh_repo = RefreshRepository(db)
    return AuthService(user_repo, refresh_repo)


def get_user_service(db: Annotated[AsyncSession, Depends(get_db)]) -> UserService:
    repo = UserRepository(db)
    return UserService(repo)


def get_department_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DepartmentService:
    repo = DepartmentRepository(db)
    return DepartmentService(repo)
