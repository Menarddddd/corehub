from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    BadRequestException,
    CredentialsException,
    DuplicateEntryException,
    FieldNotFoundException,
)
from app.core.security import hash_password, verify_password
from app.utils.user import clean_user_info
from app.models.users import User
from app.repositories.user import UserRepository
from app.schemas.cursor import CursorPageInfo
from app.schemas.enum import Role
from app.schemas.user import (
    ChangePassword,
    UserCreate,
    UserPageResponse,
    UserUpdate,
    UserResponse,
)
from app.utils.cursor import get_cursor_info


class UserService:

    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def get_users_service(
        self,
        department_id: UUID | None,
        role: Role | None,
        limit: int,
        cursor: str | None,
    ) -> UserPageResponse:
        conditions = []
        if department_id is not None:
            conditions.append(User.department_id == department_id)

        if role is not None:
            conditions.append(User.role == role.value)

        users = await self.repo.get_users(*conditions, limit=limit, cursor=cursor)

        users, has_next, next_cursor = get_cursor_info(users, limit)

        return UserPageResponse(
            items=[UserResponse.model_validate(user) for user in users],
            page_info=CursorPageInfo(has_next=has_next, next_cursor=next_cursor),
        )

    async def create_user_service(self, form_data: UserCreate) -> User:
        user_data = clean_user_info(form_data.model_dump())

        new_user = User(
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=hash_password(form_data.password),
            role=form_data.role,
        )

        try:
            return await self.repo.save(new_user)
        except IntegrityError as e:
            error = str(e.orig)

            if "uq_users_username" in error:
                raise DuplicateEntryException("username", user_data["username"])
            elif "uq_users_email" in error:
                raise DuplicateEntryException("email", user_data["email"])
            else:
                raise BadRequestException("Account cannot be created")

    async def get_user_service(self, user_id: UUID) -> User | None:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise FieldNotFoundException("users", str(user_id))

        return user

    async def update_user_service(self, user_id: UUID, form_data: UserUpdate) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise FieldNotFoundException("users", str(user_id))

        user_data = clean_user_info(form_data.model_dump(exclude_unset=True))

        if not user_data:
            raise BadRequestException("No fields provided to update")

        for key, value in user_data.items():
            setattr(user, key, value)

        try:
            return await self.repo.update(user)
        except IntegrityError as e:
            error = str(e.orig)

            if "uq_users_username" in error:
                raise DuplicateEntryException("username", user_data["username"])
            elif "uq_users_email" in error:
                raise DuplicateEntryException("email", user_data["email"])
            else:
                raise BadRequestException("Account cannot be updated")

    async def change_password_service(
        self, form_data: ChangePassword, current_user: User
    ) -> None:
        if not verify_password(
            form_data.current_password, current_user.hashed_password
        ):
            raise CredentialsException()

        current_user.hashed_password = hash_password(form_data.new_password)
        await self.repo.update(current_user)

    async def delete_user_service(self, user_id: UUID) -> None:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise FieldNotFoundException("users", str(user_id))

        user.deleted_at = datetime.now(timezone.utc)
        await self.repo.update(user)
