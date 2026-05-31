from typing import Annotated
from uuid import UUID
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import FieldNotFoundException, ForbiddenException
from app.core.security import get_current_user
from app.models.tasks import Task
from app.models.users import User
from app.repositories.task import TaskRepository
from app.repositories.user import UserRepository
from app.services.task import TaskService


def get_tasks_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TaskService:
    repo = TaskRepository(db)
    user_repo = UserRepository(db)
    return TaskService(repo, user_repo)


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
