from typing import Annotated
from fastapi import Depends, status
from fastapi.routing import APIRouter

from app.core.security import get_current_user
from app.dependencies.dashboard import get_dashboard_service
from app.models.users import User
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard import DashboardService

router = APIRouter()


@router.get(
    "",
    response_model=DashboardResponse,
    status_code=status.HTTP_200_OK,
)
async def get_dashboard(
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get the current user's dashboard.
    Returns user profile, task summary, unread notifications,
    unread message count, and recent announcements.
    Accessible by all authenticated roles.
    """
    return await service.get_dashboard(current_user)