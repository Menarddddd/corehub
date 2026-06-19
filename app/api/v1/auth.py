from typing import Annotated
from fastapi import Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.routing import APIRouter

from app.dependencies.auth import AuthServiceDep
from app.dependencies.user import AnyAuthenticated
from app.schemas.user import RefreshTokenRequest, Token

router = APIRouter()


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthServiceDep,
):
    """
    Authentication service for getting access token and refresh token
    Filters out deleted users
    """
    return await service.login_service(
        form_data.username,
        form_data.password,
        request.headers.get("user-agent"),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    form_data: RefreshTokenRequest,
    service: AuthServiceDep,
    current_user: AnyAuthenticated,
):
    """
    Invalidate active refresh token in db
    """
    await service.logout_service(form_data.refresh_token)


@router.post("/refresh", response_model=Token, status_code=status.HTTP_200_OK)
async def refresh(
    request: Request,
    form_data: RefreshTokenRequest,
    service: AuthServiceDep,
):
    """
    Accepts refresh token once validated.
    Generates new access and refresh token
    Revoke used refresh token
    """
    return await service.refresh_service(
        form_data.refresh_token,
        request.headers.get("user-agent"),
    )
