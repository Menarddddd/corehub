import secrets
import jwt
import hmac
import hashlib
from datetime import datetime, timedelta, timezone
from uuid import UUID
from typing import Annotated
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from pwdlib import PasswordHash

from app.core.database import get_db
from app.core.settings import settings
from app.repositories.users import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
password_hash = PasswordHash.recommended()


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user_repo = UserRepository(db)

    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"message": "invalid credentials"},
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.ACCESS_SECRET_KEY.get_secret_value(),
            algorithms=[settings.ALGORITHM],
        )

        user_id = payload.get("sub")
        if not user_id:
            raise exc

        try:
            user_id = UUID(user_id)
        except (ValueError, AttributeError):
            raise exc

        user = await user_repo.get_by_id(user_id)
        if not user:
            raise exc

        if user.deleted_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "account is deactivated"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "token has expired"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise exc


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_pwd: str, hashed_pwd: str) -> bool:
    return password_hash.verify(plain_pwd, hashed_pwd)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_MINUTES_EXPIRES
    )
    payload = jwt.encode(
        to_encode,
        settings.ACCESS_SECRET_KEY.get_secret_value(),
        algorithm=settings.ALGORITHM,
    )
    return payload


def create_refresh_token() -> str:
    raw_token = secrets.token_urlsafe()

    # saved to db later
    hashed_token = hmac.new(
        key=settings.REFRESH_SECRET_KEY.get_secret_value().encode(),
        msg=raw_token.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    return raw_token
