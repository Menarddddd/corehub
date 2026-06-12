from typing import Annotated
from uuid import UUID
from fastapi import Depends

from app.core.database import AsyncDB
from app.core.exceptions import FieldNotFoundException, ForbiddenException
from app.core.redis import ARedis
from app.core.security import GetCurrentUser
from app.models.tasks import Task
from app.repositories.notification import NotificationRepository
from app.repositories.task import TaskRepository
from app.repositories.user import UserRepository
from app.services.task import TaskService


def get_tasks_service(
    db: AsyncDB,
    redis: ARedis,
    current_user: GetCurrentUser,
) -> TaskService:
    repo = TaskRepository(db)
    user_repo = UserRepository(db)
    notif_repo = NotificationRepository(db)
    return TaskService(repo, user_repo, notif_repo, redis)


async def check_task_owner(
    task_id: UUID,
    current_user: GetCurrentUser,
    db: AsyncDB,
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


TaskServiceDep = Annotated[TaskService, Depends(get_tasks_service)]
CheckTaskOwner = Annotated[Task, Depends(check_task_owner)]
