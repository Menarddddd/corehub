import redis.asyncio as aioredis
from typing import Annotated
from uuid import UUID
from fastapi import Depends, Query, status
from fastapi.routing import APIRouter

from app.core.redis import get_redis
from app.core.security import get_current_user
from app.dependencies.user import get_user_service, required_roles
from app.models.users import User
from app.schemas.enum import Role
from app.schemas.user import (
    UserCreate,
    UserPageResponse,
    UserResponse,
    UserUpdate,
    ChangePassword,
)
from app.services.user import UserService

router = APIRouter()


@router.get("", response_model=UserPageResponse, status_code=status.HTTP_200_OK)
async def get_users(
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User, Depends(required_roles(Role.ADMIN, Role.MANAGER))],
    department_id: UUID | None = None,
    role: Role | None = None,
    limit: Annotated[int, Query(ge=1, lt=50)] = 10,
    cursor: Annotated[str | None, Query()] = None,
):
    """
    Retrieve a paginated list of all users.
    Supports optional filtering by department and role.
    Restricted to ADMIN and MANAGER roles only.
    """
    return await service.get_users_service(
        department_id, role, limit=limit, cursor=cursor
    )


@router.post(
    "/create", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def create_user(
    form_data: UserCreate,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User, Depends(required_roles(Role.ADMIN))],
):
    """
    Create a new user account.
    Username and email must be unique across the system.
    Restricted to ADMIN role only.
    """
    return await service.create_user_service(form_data)


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_profile(
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Retrieve the profile of the currently authenticated user.
    No extra DB query needed since get_current_user already
    fetches the user object from the database.
    Accessible by all authenticated roles.
    """
    return current_user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    form_data: ChangePassword,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Change the password of the currently authenticated user.
    Requires the current password for verification before updating.
    Accessible by all authenticated roles.
    """
    await service.change_password_service(form_data, current_user)


@router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user(
    user_id: UUID,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User, Depends(required_roles(Role.ADMIN, Role.MANAGER))],
):
    """
    Retrieve a single user by their ID.
    Raises 404 if the user does not exist.
    Restricted to ADMIN and MANAGER roles only.
    """
    return await service.get_user_service(user_id)


@router.patch("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user(
    user_id: UUID,
    form_data: UserUpdate,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User, Depends(required_roles(Role.ADMIN, Role.MANAGER))],
):
    """
    Update the details of a specific user.
    Only fields included in the request body will be updated.
    Username and email must remain unique.
    Raises 404 if the user does not exist.
    Restricted to ADMIN and MANAGER roles only.
    """
    return await service.update_user_service(user_id, form_data)


@router.post("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User, Depends(required_roles(Role.ADMIN))],
):
    """
    Soft delete a user by setting their deleted_at timestamp.
    The user record is retained in the database for audit purposes.
    The user will no longer be able to authenticate after deletion.
    Raises 404 if the user does not exist.
    Restricted to ADMIN role only.
    """
    await service.delete_user_service(user_id)
