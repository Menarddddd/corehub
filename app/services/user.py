import json
import redis.asyncio as aioredis
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    BadRequestException,
    CredentialsException,
    DuplicateEntryException,
    FieldNotFoundException,
)
from app.core.redis import get_redis
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

    def __init__(self, repo: UserRepository, redis: aioredis.Redis):
        self.repo = repo
        self.redis = redis

    async def _build_users_cache_key(
        self,
        department_id: UUID | None,
        role: Role | None,
        limit: int,
        cursor: str | None,
    ) -> str:
        """
        Build a unique cache key based on the query parameters.
        Each unique combination of filters = unique key.
        """
        dept = str(department_id) if department_id else "all"
        r = role.value if role else "all"
        c = cursor if cursor else "none"

        return f"users:dept:{dept}:role:{r}:limit:{limit}:cursor:{c}"

    async def get_users_service(
        self,
        department_id: UUID | None,
        role: Role | None,
        limit: int,
        cursor: str | None,
    ) -> UserPageResponse:
        """
        Fetch all users with optional filters and cursor-based pagination.
        Builds conditions dynamically based on provided filter arguments.
        Only adds a condition if the filter value is not None.
        """
        cache_key = await self._build_users_cache_key(
            department_id=department_id,
            role=role,
            limit=limit,
            cursor=cursor,
        )

        cached_data = await self.redis.get(cache_key)

        if cached_data:
            data = json.loads(cached_data)
            return UserPageResponse(**data)

        conditions = []

        if department_id is not None:
            conditions.append(User.department_id == department_id)

        if role is not None:
            conditions.append(User.role == role.value)

        users = await self.repo.get_users(*conditions, limit=limit, cursor=cursor)
        users, has_next, next_cursor = get_cursor_info(users, limit)

        response = UserPageResponse(
            items=[UserResponse.model_validate(user) for user in users],
            page_info=CursorPageInfo(has_next=has_next, next_cursor=next_cursor),
        )

        # response.model_dump() converts Pydantic model to dict
        # json.dumps() with default=str handles UUID and datetime
        await self.redis.set(
            cache_key,
            json.dumps(response.model_dump(), default=str),
            ex=300,  # Cache for 5 minutes
        )

        return response

    async def create_user_service(self, form_data: UserCreate) -> User:
        """
        Create a new user account with a hashed password.
        Strips and normalizes user input before saving.
        Raises 409 if the username or email already exists.
        Raises 400 for any other integrity error.
        """
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

    async def get_user_service(self, user_id: UUID) -> User:
        """
        Fetch a single user by their ID.
        Raises 404 if the user does not exist.
        """
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise FieldNotFoundException("users", str(user_id))
        return user

    async def update_user_service(self, user_id: UUID, form_data: UserUpdate) -> User:
        """
        Update allowed fields of an existing user.
        Uses exclude_unset=True so only explicitly provided
        fields are applied to the user object.
        Strips and normalizes user input before saving.
        Raises 404 if the user does not exist.
        Raises 400 if no fields are provided in the request body.
        Raises 409 if the new username or email is already taken.
        """
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
        """
        Change the password of the currently authenticated user.
        Verifies the current password before applying the new one.
        Raises 401 if the current password does not match.
        """
        if not verify_password(
            form_data.current_password, current_user.hashed_password
        ):
            raise CredentialsException()

        current_user.hashed_password = hash_password(form_data.new_password)
        await self.repo.update(current_user)

    async def delete_user_service(self, user_id: UUID) -> None:
        """
        Soft delete a user by setting their deleted_at timestamp to now.
        The user record is kept in the database for audit and history purposes.
        Deleted users can no longer authenticate since get_current_user
        checks for deleted_at before allowing access.
        Raises 404 if the user does not exist.
        """
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise FieldNotFoundException("users", str(user_id))

        user.deleted_at = datetime.now(timezone.utc)
        await self.repo.update(user)
