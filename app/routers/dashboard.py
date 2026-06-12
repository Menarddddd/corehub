from fastapi import status
from fastapi.routing import APIRouter

from app.dependencies.dashboard import DashboardServiceDep
from app.dependencies.user import AnyAuthenticated
from app.schemas.dashboard import DashboardResponse

router = APIRouter()


@router.get(
    "",
    response_model=DashboardResponse,
    status_code=status.HTTP_200_OK,
)
async def get_dashboard(
    service: DashboardServiceDep,
    current_user: AnyAuthenticated,
):
    """
    Get the current user's dashboard.
    Returns user profile, task summary, unread notifications,
    unread message count, and recent announcements.
    Accessible by all authenticated roles.
    """
    return await service.get_dashboard(current_user)
