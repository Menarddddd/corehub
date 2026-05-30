from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.department import DepartmentRepository
from app.repositories.user import UserRepository
from app.services.department import DepartmentService


def get_department_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DepartmentService:
    """Wire DepartmentRepository and UserRepository into DepartmentService."""
    repo = DepartmentRepository(db)
    user_repo = UserRepository(db)
    return DepartmentService(repo, user_repo)
