from fastapi import APIRouter

from app.routers.auth import router as auth_router
from app.routers.user import router as user_router
from app.routers.department import router as department_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(user_router, prefix="/users", tags=["users"])
api_router.include_router(department_router, prefix="/departments", tags=["department"])
