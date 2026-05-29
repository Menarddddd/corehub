from typing import Annotated
from uuid import UUID
from fastapi import Depends, Query, status
from fastapi.routing import APIRouter

from app.core.dependencies import (
    get_tasks_service,
    required_roles,
)
from app.core.security import get_current_user
from app.models.users import User
from app.schemas.enum import Role

from app.schemas.task import TaskCreate, TaskPageResponse, TaskResponse, TaskUpdate
from app.services.task import TaskService

router = APIRouter()


@router.get("", response_model=TaskPageResponse, status_code=status.HTTP_200_OK)
async def get_tasks(
    service: Annotated[TaskService, Depends(get_tasks_service)],
    current_user: Annotated[User, Depends(required_roles(Role.ADMIN, Role.MANAGER))],
    limit: Annotated[int, Query(ge=1, lt=50)] = 10,
    cursor: Annotated[str | None, Query()] = None,
):
    return await service.get_tasks_service(limit, cursor)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    form_data: TaskCreate,
    service: Annotated[TaskService, Depends(get_tasks_service)],
    current_user: Annotated[User, Depends(required_roles(Role.ADMIN, Role.MANAGER))],
):
    return await service.create_task_service(form_data, current_user)


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
)
async def get_task(
    task_id: UUID,
    service: Annotated[TaskService, Depends(get_tasks_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await service.get_task_service(task_id)


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
)
async def update_task(
    task_id: UUID,
    form_data: TaskUpdate,
    service: Annotated[TaskService, Depends(get_tasks_service)],
    current_user: Annotated[User, Depends(required_roles(Role.ADMIN, Role.MANAGER))],
):
    return await service.update_task_service(task_id, form_data)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def task_department(
    task_id: UUID,
    service: Annotated[TaskService, Depends(get_tasks_service)],
    current_user: Annotated[User, Depends(required_roles(Role.ADMIN, Role.MANAGER))],
):
    return await service.delete_task_service(task_id)
