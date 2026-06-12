from typing import Annotated

from fastapi import Depends

from app.core.database import AsyncDB
from app.core.redis import ARedis
from app.core.security import GetCurrentUser
from app.repositories.department import DepartmentRepository
from app.repositories.user import UserRepository
from app.services.department import DepartmentService


def get_department_service(
    db: AsyncDB,
    redis: ARedis,
    current_user: GetCurrentUser,
) -> DepartmentService:
    """Wire DepartmentRepository and UserRepository into DepartmentService."""
    repo = DepartmentRepository(db)
    user_repo = UserRepository(db)
    return DepartmentService(repo, user_repo, redis)


DepartmentServiceDep = Annotated[DepartmentService, Depends(get_department_service)]
