from typing import Annotated
from fastapi import Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.routing import APIRouter

from app.core.security import get_current_user
from app.dependencies.auth import get_auth_service
from app.models.users import User
from app.schemas.user import RefreshTokenRequest, Token
from app.services.auth import AuthService

router = APIRouter()


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    return await service.login_service(
        form_data.username,
        form_data.password,
        request.headers.get("user-agent"),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    form_data: RefreshTokenRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await service.logout_service(form_data.refresh_token)


@router.post("/refresh", response_model=Token, status_code=status.HTTP_200_OK)
async def refresh(
    request: Request,
    form_data: RefreshTokenRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    return await service.refresh_service(
        form_data.refresh_token,
        request.headers.get("user-agent"),
    )
