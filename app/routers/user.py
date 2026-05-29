from typing import Annotated
from uuid import UUID
from fastapi import Depends, Query, status
from fastapi.routing import APIRouter

from app.core.dependencies import get_user_service, required_roles
from app.core.security import get_current_user
from app.models.users import User
from app.schemas.enum import Role
from app.schemas.user import (
    UserCreate,
    UserPageResponse,
    UserResponse,
    UserUpdate,
    ChangePassword,
)
from app.services.users import UserService

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
    return await service.create_user_service(form_data)


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_profile(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    form_data: ChangePassword,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await service.change_password_service(form_data, current_user)


@router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user(
    user_id: UUID,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User, Depends(required_roles(Role.ADMIN, Role.MANAGER))],
):
    return await service.get_user_service(user_id)


@router.patch("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user(
    user_id: UUID,
    form_data: UserUpdate,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User, Depends(required_roles(Role.ADMIN, Role.MANAGER))],
):
    return await service.update_user_service(user_id, form_data)


@router.post("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User, Depends(required_roles(Role.ADMIN))],
):
    await service.delete_user_service(user_id)
