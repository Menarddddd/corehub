from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    BadRequestException,
    DuplicateEntryException,
    FieldNotFoundException,
)
from app.models.departments import Department
from app.models.users import User
from app.repositories.department import DepartmentRepository
from app.repositories.user import UserRepository
from app.schemas.cursor import CursorPageInfo
from app.schemas.department import (
    DepartmentCreate,
    DepartmentPageResponse,
    DepartmentResponse,
    DepartmentUpdate,
    DepartmentWithUserPageResponse,
)
from app.schemas.user import UserResponse
from app.utils.cursor import get_cursor_info


class DepartmentService:
    def __init__(
        self,
        repo: DepartmentRepository,
        user_repo: UserRepository,
    ):
        self.repo = repo
        self.user_repo = user_repo

    async def get_departments_service(
        self,
        limit: int,
        cursor: str | None,
        name: str | None = None,
    ) -> DepartmentPageResponse:
        """
        Fetch all departments with optional name filter
        and cursor-based pagination.
        Builds conditions dynamically based on provided arguments.
        """
        conditions = []

        if name is not None:
            # Case-insensitive name search
            conditions.append(Department.name.ilike(f"%{name}%"))

        departments = await self.repo.get_departments(
            *conditions, limit=limit, cursor=cursor
        )
        departments, has_next, next_cursor = get_cursor_info(departments, limit)

        return DepartmentPageResponse(
            items=[DepartmentResponse.model_validate(dept) for dept in departments],
            page_info=CursorPageInfo(has_next=has_next, next_cursor=next_cursor),
        )

    async def get_department_service(self, department_id: UUID) -> Department:
        """
        Fetch a single department by its ID.
        Raises 404 if the department does not exist.
        """
        department = await self.repo.get_by_id(department_id)
        if not department:
            raise FieldNotFoundException("departments", str(department_id))
        return department

    async def create_department_service(
        self, form_data: DepartmentCreate
    ) -> Department:
        """
        Create a new department.
        Raises 409 if a department with the same name already exists.
        """
        try:
            new_department = Department(name=form_data.name)
            return await self.repo.save(new_department)
        except IntegrityError:
            raise DuplicateEntryException("departments", form_data.name)

    async def get_department_users_service(
        self,
        department_id: UUID,
        limit: int,
        cursor: str | None,
    ) -> DepartmentWithUserPageResponse:
        """
        Fetch a department and its users with cursor-based pagination.
        First validates the department exists.
        Then fetches users in that department in paginated chunks.
        """
        department = await self.repo.get_by_id(department_id)
        if not department:
            raise FieldNotFoundException("departments", str(department_id))

        users = await self.user_repo.get_users(
            User.department_id == department_id,
            limit=limit,
            cursor=cursor,
        )

        users, has_next, next_cursor = get_cursor_info(users, limit)

        return DepartmentWithUserPageResponse(
            department=DepartmentResponse.model_validate(department),
            items=[UserResponse.model_validate(user) for user in users],
            page_info=CursorPageInfo(has_next=has_next, next_cursor=next_cursor),
        )

    async def update_department_service(
        self,
        department_id: UUID,
        form_data: DepartmentUpdate,
    ) -> Department:
        """
        Update the details of an existing department.
        Uses exclude_unset=True so only fields included
        in the request body are updated.
        Raises 404 if the department does not exist.
        Raises 400 if no fields are provided.
        Raises 409 if the new name is already taken.
        """
        department_data = form_data.model_dump(exclude_unset=True)
        if not department_data:
            raise BadRequestException("No fields to update")

        department = await self.repo.get_by_id(department_id)
        if not department:
            raise FieldNotFoundException("departments", str(department_id))

        for key, val in department_data.items():
            setattr(department, key, val)

        try:
            return await self.repo.update(department)
        except IntegrityError:
            raise DuplicateEntryException(
                "departments", department_data.get("name", "")
            )

    async def delete_department_service(self, department_id: UUID) -> None:
        """
        Delete a department by its ID.
        Due to SET NULL cascade, all users in this department
        will have their department_id set to NULL automatically.
        Raises 404 if the department does not exist.
        """
        department = await self.repo.get_by_id(department_id)
        if not department:
            raise FieldNotFoundException("departments", str(department_id))
        await self.repo.delete(department)

    async def assign_user_service(
        self, department_id: UUID, user_id: UUID
    ) -> Department:
        """
        Assign a user to a department by updating their department_id.
        Raises 404 if the department or user does not exist.
        Raises 400 if the user is already in this department.
        """
        department = await self.repo.get_by_id(department_id)
        if not department:
            raise FieldNotFoundException("departments", str(department_id))

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise FieldNotFoundException("users", str(user_id))

        # Prevent re-assigning to same department
        if user.department_id == department_id:
            raise BadRequestException("User is already assigned to this department")

        user.department_id = department_id
        await self.user_repo.update(user)

        return department

    async def remove_user_service(self, department_id: UUID, user_id: UUID) -> None:
        """
        Remove a user from a department by setting their department_id to NULL.
        Raises 404 if the department or user does not exist.
        Raises 400 if the user is not currently in this department.
        """
        department = await self.repo.get_by_id(department_id)
        if not department:
            raise FieldNotFoundException("departments", str(department_id))

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise FieldNotFoundException("users", str(user_id))

        # Make sure the user is actually in this department
        if user.department_id != department_id:
            raise BadRequestException("User is not assigned to this department")

        user.department_id = None
        await self.user_repo.update(user)
