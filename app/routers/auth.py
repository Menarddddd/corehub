from typing import Annotated
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.routing import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.users import Token
from app.services.auth import login_service

router = APIRouter()


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await login_service(form_data.username, form_data.password, db)


@router.post("/refresh", response_model=Token, status_code=status.HTTP_200_OK)
async def refresh(token):
    pass
