from datetime import datetime, timedelta, timezone

from app.core.settings import settings
from app.core.exceptions import BadRequestException, CredentialsException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
    verify_password,
)
from app.models.refresh_tokens import RefreshToken
from app.repositories.refresh_token import RefreshRepository
from app.repositories.user import UserRepository


class AuthService:

    def __init__(self, user_repo: UserRepository, refresh_repo: RefreshRepository):
        self.user_repo = user_repo
        self.refresh_repo = refresh_repo

    async def login_service(self, username: str, password: str, user_agent: str | None):
        user = await self.user_repo.get_by_username(username.lower())
        if not user or not verify_password(password, user.hashed_password):
            raise CredentialsException()

        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token()

        db_token = RefreshToken(
            user_id=user.id,
            hashed_token=hash_refresh_token(refresh_token),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.REFRESH_DAYS_EXPIRES),
            user_agent=user_agent,
        )

        await self.refresh_repo.save(db_token)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    async def logout_service(self, token: str) -> None:
        hashed_token = hash_refresh_token(token)

        db_token = await self.refresh_repo.get_refresh_token(hashed_token)
        if db_token:
            db_token.revoked = True
            await self.refresh_repo.update(db_token)

    async def refresh_service(self, token: str, user_agent: str | None):
        db_token = await self.refresh_repo.get_refresh_token(hash_refresh_token(token))
        if not db_token:
            raise BadRequestException("Invalid refresh token")

        if db_token.revoked:
            raise BadRequestException("Revoked refresh token")

        if db_token.expires_at < datetime.now(timezone.utc):
            raise BadRequestException("Expired refresh token")

        user = await self.user_repo.get_by_id(db_token.user_id)

        if not user:
            raise BadRequestException("User not found")

        if user.deleted_at:
            raise BadRequestException("Account is deactivated")

        db_token.revoked = True
        await self.refresh_repo.update(db_token)

        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token()

        db_token = RefreshToken(
            user_id=user.id,
            hashed_token=hash_refresh_token(refresh_token),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.REFRESH_DAYS_EXPIRES),
            user_agent=user_agent,
        )

        # await self.refresh_repo.save(db_token)  uncomment after development

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
