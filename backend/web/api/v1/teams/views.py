from fastapi import HTTPException, APIRouter, Depends
from uuid import UUID
from backend.web.api.v1.teams.schema import TeamResponse, UpdateTeamRequest, CreateTeamRequest
from backend.db.dependencies import get_db_session
from backend.services.auth.dependency import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.teams.crud import create_team, get_team, update_team, delete_team, get_teams_by_user_id

router = APIRouter()


@router.post("/team", response_model=dict)
async def create_team_endpoint(
    request: CreateTeamRequest, 
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    """
    Создание новой команды.

    Аргументы:
    - request (CreateTeamRequest): Запрос с названием команды.
    - db (AsyncSession): Сессия базы данных, полученная через Depends.
    - current_user (User): Текущий пользователь, полученный через Depends.

    Возвращает:
    - dict: Идентификатор созданной команды.
    """
    team_id = await create_team(request.title, current_user.id, db)
    return {"team_id": team_id}

@router.get("/team/{team_id}", response_model=TeamResponse)
async def get_team_endpoint(
    team_id: UUID, 
    db: AsyncSession = Depends(get_db_session), 
    current_user = Depends(get_current_user)
):
    """
    Получение информации о команде по идентификатору.

    Аргументы:
    - team_id (UUID): Идентификатор команды.
    - db (AsyncSession): Сессия базы данных, полученная через Depends.
    - current_user (User): Текущий пользователь, полученный через Depends.

    Возвращает:
    - TeamResponse: Данные о команде, пользователях и проектах.
    """
    team = await get_team(team_id, db)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

@router.put("/team", response_model=TeamResponse)
async def update_team_endpoint(
    request: UpdateTeamRequest, 
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    """
    Изменение данных команды.

    Аргументы:
    - request (UpdateTeamRequest): Данные для обновления команды (id, title, status, users, projects).
    - db (AsyncSession): Сессия базы данных, полученная через Depends.
    - current_user (User): Текущий пользователь, полученный через Depends.

    Возвращает:
    - TeamResponse: Обновленные данные команды.
    """
    updated_team = await update_team(request, current_user.id, db)
    if not updated_team:
        raise HTTPException(status_code=404, detail="Team not found")
    return updated_team

@router.delete("/team/{team_id}", response_model=dict)
async def delete_team_endpoint(
    team_id: UUID, 
    db: AsyncSession = Depends(get_db_session), 
    current_user = Depends(get_current_user)
):
    """
    Удаление команды по идентификатору.

    Аргументы:
    - team_id (UUID): Идентификатор команды.
    - db (AsyncSession): Сессия базы данных, полученная через Depends.
    - current_user (User): Текущий пользователь, полученный через Depends.

    Возвращает:
    - dict: Сообщение о результате удаления.
    """
    deleted = await delete_team(team_id, current_user.id, db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Team not found")
    return {"detail": "Team deleted successfully"}


@router.get("/teams")
async def get_user_teams(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Возвращает список команд пользователя.
    """
    teams = await get_teams_by_user_id(db, current_user.id)
    return teams