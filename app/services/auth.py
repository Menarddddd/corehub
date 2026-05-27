from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CredentialsException
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.repositories.users import UserRepository


async def login_service(username: str, password: str, db: AsyncSession):
    user_repo = UserRepository(db)

    user = await user_repo.get_by_username(username)
    if not user or not verify_password(password, user.hashed_password):
        raise CredentialsException()

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }
