from app.core.database import AsyncSessionLocal
from app.repositories.dashboard import DashboardRepository
from app.services.dashboard import DashboardService


async def get_dashboard_service() -> DashboardService:
    repo = DashboardRepository(session_factory=AsyncSessionLocal)
    return DashboardService(repo=repo)