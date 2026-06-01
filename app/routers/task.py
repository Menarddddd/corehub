import redis.asyncio as aioredis
from typing import Annotated
from uuid import UUID
from fastapi import Depends, Query, status
from fastapi.routing import APIRouter

from app.core.security import get_current_user
from app.dependencies.task import check_task_owner, get_tasks_service
from app.dependencies.user import required_roles
from app.models.tasks import Task
from app.models.users import User
from app.schemas.enum import Role, TaskDue, TaskPriority, TaskStatus, TaskView
from app.schemas.task import (
    TaskCreate,
    TaskDueDateUpdate,
    TaskPageResponse,
    TaskResponse,
    TaskStatusChange,
    TaskUpdate,
)
from app.services.task import TaskService

router = APIRouter()


@router.get("", response_model=TaskPageResponse, status_code=status.HTTP_200_OK)
async def get_tasks(
    service: Annotated[TaskService, Depends(get_tasks_service)],
    current_user: Annotated[User, Depends(required_roles(Role.ADMIN, Role.MANAGER))],
    status: Annotated[TaskStatus | None, Query()] = None,
    priority: Annotated[TaskPriority | None, Query()] = None,
    due: Annotated[TaskDue | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, lt=50)] = 10,
    cursor: Annotated[str | None, Query()] = None,
):
    """
    Retrieve a paginated list of ALL tasks in the system.
    Supports optional filtering by status, priority, and due date range.
    Restricted to ADMIN and MANAGER roles only.
    """
    return await service.get_tasks_service(
        status=status,
        priority=priority,
        due=due,
        limit=limit,
        cursor=cursor,
    )


@router.get("/my", response_model=TaskPageResponse, status_code=status.HTTP_200_OK)
async def get_my_tasks(
    service: Annotated[TaskService, Depends(get_tasks_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    task_view: Annotated[TaskView | None, Query()] = None,
    status: Annotated[TaskStatus | None, Query()] = None,
    priority: Annotated[TaskPriority | None, Query()] = None,
    due: Annotated[TaskDue | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, lt=50)] = 10,
    cursor: Annotated[str | None, Query()] = None,
):
    """
    Retrieve a paginated list of the current user's tasks.
    Use task_view=assigned to see tasks assigned to you.
    Use task_view=created to see tasks you created.
    If task_view is omitted, defaults to showing assigned tasks.
    Supports optional filtering by status, priority, and due date range.
    Accessible by all authenticated roles.
    Uses caching with TTL of 180 or 3 mins
    """
    return await service.get_user_tasks_service(
        current_user.id,
        task_view=task_view,
        status=status,
        priority=priority,
        due=due,
        limit=limit,
        cursor=cursor,
    )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    form_data: TaskCreate,
    service: Annotated[TaskService, Depends(get_tasks_service)],
    current_user: Annotated[User, Depends(required_roles(Role.ADMIN, Role.MANAGER))],
):
    """
    Create and assign a new task to a user.
    Managers can only assign tasks to employees, not other managers or admins.
    Admins can assign to anyone except themselves.
    Self-assignment is not allowed for any role.
    Restricted to ADMIN and MANAGER roles only.
    """
    return await service.create_task_service(form_data, current_user)


@router.get(
    "/my/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
)
async def get_my_task(
    task_id: UUID,
    service: Annotated[TaskService, Depends(get_tasks_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Retrieve a single task that is assigned to the current user.
    Returns 403 if the task exists but belongs to a different user.
    Accessible by all authenticated roles.
    """
    return await service.get_my_task_service(task_id, current_user)


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
)
async def get_task(
    task_id: UUID,
    service: Annotated[TaskService, Depends(get_tasks_service)],
    current_user: Annotated[User, Depends(required_roles(Role.ADMIN, Role.MANAGER))],
):
    """
    Retrieve a single task by its ID.
    Restricted to ADMIN and MANAGER roles only.
    """
    return await service.get_task_service(task_id)


@router.get(
    "/{user_id}/all", response_model=TaskPageResponse, status_code=status.HTTP_200_OK
)
async def get_user_tasks(
    user_id: UUID,
    service: Annotated[TaskService, Depends(get_tasks_service)],
    current_user: Annotated[User, Depends(required_roles(Role.ADMIN, Role.MANAGER))],
    task_view: Annotated[TaskView | None, Query()] = None,
    status: Annotated[TaskStatus | None, Query()] = None,
    priority: Annotated[TaskPriority | None, Query()] = None,
    due: Annotated[TaskDue | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, lt=50)] = 10,
    cursor: Annotated[str | None, Query()] = None,
):
    """
    Retrieve a paginated list of ALL tasks of the user_id specified.
    Supports optional filtering by status, priority, and due date range.
    Restricted to ADMIN and MANAGER roles only.
    Uses caching with TTL of 180 or 3 mins
    """
    return await service.get_user_tasks_service(
        user_id=user_id,
        task_view=task_view,
        status=status,
        priority=priority,
        due=due,
        limit=limit,
        cursor=cursor,
    )


@router.patch(
    "/due-date/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
)
async def update_task_due_date(
    form_data: TaskDueDateUpdate,
    task: Annotated[Task, Depends(check_task_owner)],
    service: Annotated[TaskService, Depends(get_tasks_service)],
    current_user: Annotated[User, Depends(required_roles(Role.ADMIN, Role.MANAGER))],
):
    """
    Update the due date of a specific task.
    Only the original task creator can change the due date.
    Due date must always be set to a future date.
    Restricted to ADMIN and MANAGER roles only.
    """
    return await service.update_due_date_service(task, form_data.due_date)


@router.patch(
    "/status/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
)
async def update_status_task(
    task_id: UUID,
    form_data: TaskStatusChange,
    service: Annotated[TaskService, Depends(get_tasks_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Update the status of a specific task.
    Employees can only update the status of tasks assigned to them.
    Admins and Managers can update status of any task.
    Accessible by all authenticated roles.
    """
    return await service.update_status_task_service(task_id, form_data, current_user)


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
)
async def update_task(
    form_data: TaskUpdate,
    task: Annotated[Task, Depends(check_task_owner)],
    service: Annotated[TaskService, Depends(get_tasks_service)],
    current_user: Annotated[User, Depends(required_roles(Role.ADMIN, Role.MANAGER))],
):
    """
    Update the details of a specific task (title, description, priority, etc).
    Only the original task creator can modify the task details.
    Restricted to ADMIN and MANAGER roles only.
    """
    return await service.update_task_service(task, form_data)


@router.delete("/my/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_task(
    task: Annotated[Task, Depends(check_task_owner)],
    service: Annotated[TaskService, Depends(get_tasks_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Delete a task created by the current user.
    Only the original task creator can delete their own task.
    Since only ADMIN and MANAGER can create tasks,
    only they will ever reach this endpoint successfully.
    """
    await service.delete_my_task_service(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    service: Annotated[TaskService, Depends(get_tasks_service)],
    current_user: Annotated[User, Depends(required_roles(Role.ADMIN))],
):
    """
    Hard delete any task by its ID regardless of ownership.
    This action is permanent and cannot be undone.
    Restricted to ADMIN role only.
    """
    await service.delete_task_service(task_id)
