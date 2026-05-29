from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    BadRequestException,
    DuplicateEntryException,
    FieldNotFoundException,
)
from app.models.departments import Department
from app.repositories.department import DepartmentRepository
from app.schemas.cursor import CursorPageInfo
from app.schemas.department import (
    DepartmentCreate,
    DepartmentPageResponse,
    DepartmentUpdate,
    DepartmentResponse,
)
from app.utils.cursor import get_cursor_info


class DepartmentService:
    def __init__(self, repo: DepartmentRepository):
        self.repo = repo

    async def get_departments_service(
        self, limit: int, cursor: str | None
    ) -> DepartmentPageResponse:
        departments = await self.repo.get_departments(limit=limit, cursor=cursor)

        departments, has_next, next_cursor = get_cursor_info(departments, limit)

        return DepartmentPageResponse(
            items=[
                DepartmentResponse.model_validate(department)
                for department in departments
            ],
            page_info=CursorPageInfo(has_next=has_next, next_cursor=next_cursor),
        )

    async def get_department_service(self, department_id: UUID) -> Department | None:
        department = await self.repo.get_by_id(department_id)
        if not department:
            raise FieldNotFoundException("department", str(department_id))

        return department

    async def create_department_service(
        self, form_data: DepartmentCreate
    ) -> Department:
        try:
            new_department = Department(name=form_data.name)
            return await self.repo.save(new_department)

        except IntegrityError:
            raise DuplicateEntryException("department", form_data.name)

    async def update_department_service(
        self,
        department_id: UUID,
        form_data: DepartmentUpdate,
    ) -> Department:
        department_data = form_data.model_dump()
        if not department_data:
            raise BadRequestException("No fields to update")

        department = await self.repo.get_by_id(department_id)
        if not department:
            raise FieldNotFoundException("department", str(department_id))

        for key, val in department_data.items():
            setattr(department, key, val)

        return await self.repo.update(department)

    async def delete_department_service(self, department_id: UUID) -> None:
        department = await self.repo.get_by_id(department_id)
        if not department:
            raise FieldNotFoundException("department", str(department_id))

        await self.repo.delete(department)
