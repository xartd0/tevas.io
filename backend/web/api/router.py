from fastapi.routing import APIRouter

from backend.settings import settings
from backend.web.api.v1 import docs, monitoring, user, teams

api_router = APIRouter()

# Применяем версию ко всем маршрутам
api_router.include_router(
    monitoring.router,
    prefix=f"/{settings.api_version}/monitoring",
    tags=["monitoring"],
)
api_router.include_router(docs.router, prefix=f"/{settings.api_version}", tags=["docs"])
api_router.include_router(user.router, prefix=f"/{settings.api_version}/user", tags=["user"])
api_router.include_router(teams.router, prefix=f"/{settings.api_version}", tags=["teams"])