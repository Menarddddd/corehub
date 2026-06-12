from typing import Annotated
from uuid import UUID
from fastapi import Query, status
from fastapi.routing import APIRouter

from app.dependencies.department import DepartmentServiceDep
from app.dependencies.user import AdminOnly, AdminOrManager
from app.schemas.department import (
    DepartmentCreate,
    DepartmentPageResponse,
    DepartmentResponse,
    DepartmentUpdate,
    DepartmentWithUserPageResponse,
)

router = APIRouter()


@router.get("", response_model=DepartmentPageResponse, status_code=status.HTTP_200_OK)
async def get_departments(
    service: DepartmentServiceDep,
    current_user: AdminOrManager,
    limit: Annotated[int, Query(ge=1, lt=50)] = 10,
    cursor: Annotated[str | None, Query()] = None,
    name: Annotated[str | None, Query()] = None,
):
    """
    Retrieve a paginated list of all departments.
    Supports optional filtering by department name.
    Restricted to ADMIN and MANAGER role only.
    """
    return await service.get_departments_service(limit, cursor, name)


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    form_data: DepartmentCreate,
    service: DepartmentServiceDep,
    current_user: AdminOnly,
):
    """
    Create a new department.
    Department names must be unique across the system.
    Restricted to ADMIN role only.
    """
    return await service.create_department_service(form_data)


@router.get(
    "/{department_id}/users",
    response_model=DepartmentWithUserPageResponse,
    status_code=status.HTTP_200_OK,
)
async def get_department_users(
    department_id: UUID,
    service: DepartmentServiceDep,
    current_user: AdminOrManager,
    limit: Annotated[int, Query(ge=1, lt=50)] = 10,
    cursor: Annotated[str | None, Query()] = None,
):
    """
    Retrieve a department and its assigned users with cursor-based pagination.
    Accessible by ADMIN and MANAGER roles.
    """
    return await service.get_department_users_service(
        department_id, limit=limit, cursor=cursor
    )


@router.get(
    "/{department_id}",
    response_model=DepartmentResponse,
    status_code=status.HTTP_200_OK,
)
async def get_department(
    department_id: UUID,
    service: DepartmentServiceDep,
    current_user: AdminOrManager,
):
    """
    Retrieve a single department by its ID.
    Accessible by ADMIN and MANAGER roles.
    """
    return await service.get_department_service(department_id)


@router.patch(
    "/{department_id}",
    response_model=DepartmentResponse,
    status_code=status.HTTP_200_OK,
)
async def update_department(
    department_id: UUID,
    form_data: DepartmentUpdate,
    service: DepartmentServiceDep,
    current_user: AdminOnly,
):
    """
    Update the details of an existing department.
    Only fields included in the request body will be updated.
    Department names must remain unique.
    Restricted to ADMIN role only.
    """
    return await service.update_department_service(department_id, form_data)


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    department_id: UUID,
    service: DepartmentServiceDep,
    current_user: AdminOnly,
):
    """
    Delete a department by its ID.
    Users assigned to this department will have their
    department_id set to NULL (SET NULL cascade).
    Restricted to ADMIN role only.
    """
    return await service.delete_department_service(department_id)


@router.patch(
    "/{department_id}/assign/{user_id}",
    response_model=DepartmentResponse,
    status_code=status.HTTP_200_OK,
)
async def assign_user_to_department(
    department_id: UUID,
    user_id: UUID,
    service: DepartmentServiceDep,
    current_user: AdminOnly,
):
    """
    Assign a user to a specific department.
    Raises 404 if the department or user does not exist.
    Restricted to ADMIN role only.
    """
    return await service.assign_user_service(department_id, user_id)


@router.patch(
    "/{department_id}/remove/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_user_from_department(
    department_id: UUID,
    user_id: UUID,
    service: DepartmentServiceDep,
    current_user: AdminOnly,
):
    """
    Remove a user from a specific department.
    Sets the user's department_id to NULL.
    Raises 404 if the department or user does not exist.
    Restricted to ADMIN role only.
    """
    await service.remove_user_service(department_id, user_id)
