from fastapi import HTTPException, APIRouter, Depends
from uuid import UUID
from backend.web.api.v1.teams.schema import DeactivateInvitationResponse, TeamResponse, UpdateTeamRequest, CreateTeamRequest, InvitationAcceptResponse, InvitationCreateRequest, InvitationCreateResponse
from backend.db.dependencies import get_db_session
from backend.services.auth.dependency import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.teams.crud import (
    add_user_to_team, create_team, get_team, update_team, delete_team,
    get_teams_by_user_id, get_invitation_by_id, create_invitation,
    deactivate_invitation, get_user_role_in_team, get_invitations_by_team,
    deactivate_invitation_by_id, delete_invitation
)
from datetime import datetime, timezone
from typing import List

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


@router.post("/team/invitation", response_model=InvitationCreateResponse, summary="Создание ссылки-приглашения")
async def create_team_invitation(
    request: InvitationCreateRequest, 
    current_user=Depends(get_current_user), 
    db: AsyncSession = Depends(get_db_session)
):
    """
    Создает новое приглашение в команду.
    
    Аргументы:
        request: Тело запроса с данными для создания приглашения.
        current_user: Текущий авторизованный пользователь.
        db: Сессия базы данных.

    Возвращает:
        Идентификатор приглашения и статус активности.
    """
    # Проверяем роль пользователя в команде
    user_role = await get_user_role_in_team(db, current_user.id, request.team_id)
    
    if user_role is None: 
        raise HTTPException(status_code=403, detail="User is not a member of this team.")
    
    if user_role <= 2:
        raise HTTPException(status_code=403, detail="User does not have permission to invite others.")
    
    invitation = await create_invitation(
        db=db,
        team_id=request.team_id,
        role_id=request.role_id,
        inviting_user_id=current_user.id,
        ttl_sec=request.ttl_sec
    )

    return invitation


@router.get("/team/invitation/{invitation_id}", response_model=InvitationAcceptResponse, summary="Принятие приглашения в команду")
async def accept_team_invitation(
    invitation_id: UUID, 
    current_user=Depends(get_current_user), 
    db: AsyncSession = Depends(get_db_session)
):
    """
    Принимает приглашение в команду по идентификатору.

    Аргументы:
        invitation_id: Уникальный идентификатор приглашения.
        current_user: Текущий авторизованный пользователь.
        db: Сессия базы данных.

    Возвращает:
        Сообщение о принятии приглашения и информацию о команде.
    """
    invitation = await get_invitation_by_id(db=db, invitation_id=invitation_id)

    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    user_role = await get_user_role_in_team(db, current_user.id, invitation.team_id)
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    # Проверяем, истекло ли приглашение
    if (datetime.now(timezone.utc) - invitation.created_dt).total_seconds() > invitation.ttl_sec:
        raise HTTPException(status_code=400, detail="Invitation has expired")

    # Проверяем, активное ли приглашение
    if not invitation.is_active:
        raise HTTPException(status_code=400, detail="Invitation is not active")
    
    if user_role is not None:
        raise HTTPException(status_code=400, detail="User is already a member of this team.")
    
    # Добавляем пользователя в команду
    user_team_link = await add_user_to_team(
        db=db, 
        user_id=current_user.id, 
        team_id=invitation.team_id, 
        role_id=invitation.role_id
    )

    # Принимаем приглашение и деактивируем его
    invitation.users_accepted += 1
    await db.commit()

    return InvitationAcceptResponse(
        message="Invitation accepted successfully",
        team_id=user_team_link.team_id,
        role_id=user_team_link.role,
        user_accepted_count=invitation.users_accepted
    )


@router.get("/team/{team_id}/invitations", response_model=List[InvitationCreateResponse], summary="Просмотр всех приглашений команды")
async def get_team_invitations(
    team_id: UUID, 
    current_user=Depends(get_current_user), 
    db: AsyncSession = Depends(get_db_session)
):
    """
    Возвращает все приглашения для указанной команды.

    Аргументы:
        team_id: Идентификатор команды.
        current_user: Текущий пользователь.
        db: Сессия базы данных.

    Возвращает:
        Список всех приглашений для команды.
    """
    # Проверяем, что пользователь имеет доступ к команде
    user_role = await get_user_role_in_team(db, current_user.id, team_id)
    if user_role is None or user_role < 2:
        raise HTTPException(status_code=403, detail="You do not have permission to view invitations for this team.")

    invitations = await get_invitations_by_team(db=db, team_id=team_id)
    
    return invitations

@router.put("/team/invitation/{invitation_id}/toggle", response_model=DeactivateInvitationResponse, summary="Деактивация/Активация приглашения")
async def toggle_invitation(
    invitation_id: UUID, 
    current_user=Depends(get_current_user), 
    db: AsyncSession = Depends(get_db_session)
):
    """
    Деактивирует/активирует приглашение по его идентификатору.

    Аргументы:
        invitation_id: Идентификатор приглашения. 
        current_user: Текущий пользователь.
        db: Сессия базы данных.

    Возвращает:
        Сообщение об успешной деактивации/активации.
    """
    # Проверяем, что пользователь имеет доступ к приглашению
    invitation = await get_invitation_by_id(db=db, invitation_id=invitation_id)
    if invitation is None:
        raise HTTPException(status_code=404, detail="Invitation not found")

    user_role = await get_user_role_in_team(db, current_user.id, invitation.team_id)
    if user_role is None or user_role < 2:
        raise HTTPException(status_code=403, detail="You do not have permission to deactivate this invitation.")

    invitation.is_active = not invitation.is_active
    await db.commit()
    return DeactivateInvitationResponse(message="Invitation toggled successfully")


@router.delete("/team/invitation/{invitation_id}/delete", summary="Удаление приглашения")
async def delete_invitation_endpoint(
    invitation_id: UUID, 
    current_user=Depends(get_current_user), 
    db: AsyncSession = Depends(get_db_session)
):
    """
    Удаляет приглашение.

    Аргументы:
        invitation_id: Идентификатор приглашения.
        current_user: Текущий пользователь.
        db: Сессия базы данных.

    Возвращает:
        Сообщение об успешном удалении.
    """
    # Проверяем, что пользователь имеет доступ к приглашению (например, его роль выше 1)
    invitation = await get_invitation_by_id(db=db, invitation_id=invitation_id)
    if invitation is None:
        raise HTTPException(status_code=404, detail="Invitation not found")

    user_role = await get_user_role_in_team(db, current_user.id, invitation.team_id)
    if user_role is None or user_role < 2:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this invitation.")

    await delete_invitation(db=db, invitation_id=invitation_id)
    return {"message": "Invitation deleted successfully"}
