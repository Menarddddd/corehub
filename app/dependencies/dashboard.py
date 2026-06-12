from typing import Annotated

from fastapi import Depends

from app.core.database import AsyncSessionLocal
from app.core.security import GetCurrentUser
from app.repositories.dashboard import DashboardRepository
from app.services.dashboard import DashboardService


async def get_dashboard_service(current_user: GetCurrentUser) -> DashboardService:
    repo = DashboardRepository(session_factory=AsyncSessionLocal)
    return DashboardService(repo=repo)


DashboardServiceDep = Annotated[DashboardService, Depends(get_dashboard_service)]
