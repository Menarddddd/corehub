from fastapi import APIRouter

from app.routers.auth import router as auth_router
from app.routers.user import router as user_router
from app.routers.department import router as department_router
from app.routers.task import router as task_router
from app.routers.announcement import router as announcement_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(user_router, prefix="/users", tags=["users"])
api_router.include_router(
    department_router, prefix="/departments", tags=["departments"]
)
api_router.include_router(task_router, prefix="/tasks", tags=["tasks"])
api_router.include_router(
    announcement_router, prefix="/announcements", tags=["announcements"]
)
