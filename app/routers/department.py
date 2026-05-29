from typing import Annotated
from uuid import UUID
from fastapi import Depends, Query, status
from fastapi.routing import APIRouter

from app.core.dependencies import get_department_service, required_roles
from app.models.users import User
from app.schemas.department import (
    DepartmentCreate,
    DepartmentPageResponse,
    DepartmentResponse,
    DepartmentUpdate,
)
from app.schemas.enum import Role

from app.services.department import DepartmentService

router = APIRouter()


@router.get("", response_model=DepartmentPageResponse, status_code=status.HTTP_200_OK)
async def get_departments(
    service: Annotated[DepartmentService, Depends(get_department_service)],
    current_user: Annotated[User, Depends(required_roles(Role.ADMIN))],
    limit: Annotated[int, Query(ge=1, lt=50)] = 10,
    cursor: Annotated[str | None, Query()] = None,
):
    return await service.get_departments_service(limit, cursor)


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    form_data: DepartmentCreate,
    service: Annotated[DepartmentService, Depends(get_department_service)],
    current_user: Annotated[User, Depends(required_roles(Role.ADMIN))],
):
    return await service.create_department_service(form_data)


@router.get(
    "/{department_id}",
    response_model=DepartmentResponse,
    status_code=status.HTTP_200_OK,
)
async def get_department(
    department_id: UUID,
    service: Annotated[DepartmentService, Depends(get_department_service)],
    current_user: Annotated[User, Depends(required_roles(Role.ADMIN, Role.MANAGER))],
):
    return await service.get_department_service(department_id)


@router.patch(
    "/{department_id}",
    response_model=DepartmentResponse,
    status_code=status.HTTP_200_OK,
)
async def update_department(
    department_id: UUID,
    form_data: DepartmentUpdate,
    service: Annotated[DepartmentService, Depends(get_department_service)],
    current_user: Annotated[User, Depends(required_roles(Role.ADMIN))],
):
    return await service.update_department_service(department_id, form_data)


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    department_id: UUID,
    service: Annotated[DepartmentService, Depends(get_department_service)],
    current_user: Annotated[User, Depends(required_roles(Role.ADMIN))],
):
    return await service.delete_department_service(department_id)
