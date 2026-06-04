from fastapi import APIRouter

from .routes.login import router as login_router
from .routes.questions import router as questions_router

api_router = APIRouter()
api_router.include_router(login_router)
api_router.include_router(questions_router)
