from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import FieldNotFoundException, ForbiddenException
from app.core.security import get_current_user
from app.models.tasks import Task
from app.models.users import User
from app.repositories.department import DepartmentRepository
from app.repositories.task import TaskRepository
from app.repositories.user import UserRepository
from app.repositories.refresh_token import RefreshRepository
from app.schemas.enum import Role
from app.services.auth import AuthService
from app.services.department import DepartmentService
from app.services.task import TaskService
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


def get_tasks_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TaskService:
    repo = TaskRepository(db)
    return TaskService(repo)


async def check_task_owner(
    task_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Task:
    """
    Dependency that verifies the current user is the creator of the task.
    Raises 404 if the task does not exist.
    Raises 403 if the task was created by a different user.
    Used by update and delete endpoints that require ownership.
    """
    repo = TaskRepository(db)
    task = await repo.get_by_id(task_id)
    if not task:
        raise FieldNotFoundException("tasks", str(task_id))

    if task.created_by_id != current_user.id:
        raise ForbiddenException("You cannot modify or update this task!")

    return task
