from typing import Annotated
from uuid import UUID
from fastapi import Query, status
from fastapi.routing import APIRouter

from app.dependencies.task import CheckTaskOwner, TaskServiceDep
from app.dependencies.user import AdminOnly, AdminOrManager, AnyAuthenticated
from app.schemas.enum import TaskDue, TaskPriority, TaskStatus, TaskView
from app.schemas.task import (
    TaskCreate,
    TaskDueDateUpdate,
    TaskPageResponse,
    TaskResponse,
    TaskStatusChange,
    TaskUpdate,
)

router = APIRouter()


@router.get("", response_model=TaskPageResponse, status_code=status.HTTP_200_OK)
async def get_tasks(
    service: TaskServiceDep,
    current_user: AdminOrManager,
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
    service: TaskServiceDep,
    current_user: AnyAuthenticated,
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
    service: TaskServiceDep,
    current_user: AdminOrManager,
):
    """
    Create and assign a new task to a user.
    Managers can only assign tasks to members, not other managers or admins.
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
    service: TaskServiceDep,
    current_user: AnyAuthenticated,
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
    service: TaskServiceDep,
    current_user: AdminOrManager,
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
    service: TaskServiceDep,
    current_user: AdminOrManager,
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
    task: CheckTaskOwner,
    service: TaskServiceDep,
    current_user: AdminOrManager,
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
    service: TaskServiceDep,
    current_user: AnyAuthenticated,
):
    """
    Update the status of a specific task.
    Members can only update the status of tasks assigned to them.
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
    service: TaskServiceDep,
    task: CheckTaskOwner,
    current_user: AdminOrManager,
):
    """
    Update the details of a specific task (title, description, priority, etc).
    Only the original task creator can modify the task details.
    Restricted to ADMIN and MANAGER roles only.
    """
    return await service.update_task_service(task, form_data)


@router.delete("/my/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_task(
    service: TaskServiceDep,
    task: CheckTaskOwner,
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
    service: TaskServiceDep,
    current_user: AdminOnly,
):
    """
    Hard delete any task by its ID regardless of ownership.
    This action is permanent and cannot be undone.
    Restricted to ADMIN role only.
    """
    await service.delete_task_service(task_id)
