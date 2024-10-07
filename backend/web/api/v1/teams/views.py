from fastapi import HTTPException, APIRouter, Depends
from uuid import UUID
from backend.web.api.v1.teams.schema import (
    CreateTeamRequest, DeactivateInvitationResponse, InvitationAcceptResponse,
    InvitationCreateRequest, InvitationCreateResponse, TeamResponse,
    UpdateTeamRequest, UpdateUserRoleInTeamRequest, UpdateTeamSettingsRequest
)
from backend.db.dependencies import get_db_session
from backend.services.auth.dependency import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.teams.crud import (
    add_user_to_team, create_team, get_team, update_team, delete_team,
    get_teams_by_user_id, get_invitation_by_id, create_invitation,
    get_user_role_in_team, get_invitations_by_team,
    delete_invitation, delete_user_from_team
)
from datetime import datetime, timezone
from typing import List

router = APIRouter()


@router.post("/team", response_model=dict, summary="Создание команды")
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


@router.get("/team/{team_id}", response_model=TeamResponse, summary="Просмотр команды")
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


@router.delete("/team/{team_id}", response_model=dict, summary="Удаление команды")
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


@router.get("/teams", summary="Список команд")
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
    
    if user_role.role is None: 
        raise HTTPException(status_code=403, detail="User is not a member of this team.")
    
    if user_role.role <= 2:
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
    
    if user_role.role is not None:
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
    if user_role.role is None or user_role.role <= 2:
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
    if user_role.role is None or user_role.role <= 2:
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
    if user_role.role is None or user_role.role <= 2:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this invitation.")

    await delete_invitation(db=db, invitation_id=invitation_id)
    return {"message": "Invitation deleted successfully"}


@router.put("/team/{team_id}/user/{user_id}", summary="Изменение роли пользователя в команде")
async def update_user_role_in_team_endpoint(
    request: UpdateUserRoleInTeamRequest,
    current_user=Depends(get_current_user), 
    db: AsyncSession = Depends(get_db_session)
):
    """
    Изменяет роль пользователя в команде.

    Аргументы:
        team_id: Идентификатор команды.
        user_id: Идентификатор пользователя.
        role_id: Новый идентификатор роли.
        current_user: Текущий пользователь.
        db: Сессия базы данных.

    Возвращает:
        Сообщение об успешном изменении.
    """
    # Проверяем, что пользователь имеет доступ к команде (например, его роль выше 1)
    current_user_role = await get_user_role_in_team(db, current_user.id, request.team_id)
    # Проверяем, что пользователь, чью роль мы хотим изменить, находится в команде 
    user_role = await get_user_role_in_team(db, request.user_id, request.team_id)

    # 2 - админ, 3 - владелец
    # изменять роль может владелец, админ может изменять роль ниже админа
    if current_user_role.role is None:
        raise HTTPException(status_code=403, detail="You are not a member of this team.")

    if current_user_role.role <= 2 or (user_role == 2 and current_user_role.role != 3):
        raise HTTPException(status_code=403, detail="You do not have permission to edit user roles in this team.")

    if user_role is None:
        raise HTTPException(status_code=404, detail="User not found in this team.")
    
    if request.role_id == 3 and current_user_role.role != 3:
        raise HTTPException(status_code=403, detail="You do not have permission to promote this user to team owner.")
    
    if request.user_id == current_user.id:
        raise HTTPException(status_code=403, detail="You cannot change your own role.")
    
    if request.role_id == 3 and user_role.role == 3:
        current_user_role.role = 2

    # Изменяем роль
    user_role.role = request.role_id
    await db.commit()
    return {"message": "User role updated successfully"}


@router.delete("/team/{team_id}/user/{user_id}", summary="Удаление пользователя из команды")
async def delete_user_from_team_endpoint(
    team_id: UUID,
    user_id: UUID,
    current_user=Depends(get_current_user), 
    db: AsyncSession = Depends(get_db_session)
):
    """
    Удаляет пользователя из команды.

    Аргументы:
        team_id: Идентификатор команды.
        user_id: Идентификатор пользователя.
        current_user: Текущий пользователь.
        db: Сессия базы данных.

    Возвращает:
        Сообщение об успешном удалении.
    """
    # Проверяем, что пользователь имеет доступ к команде (например, его роль выше 1)
    current_user_role = await get_user_role_in_team(db, current_user.id, team_id)
    # Проверяем, что пользователь, которого мы хотим удалить, находится в команде 
    user_role = await get_user_role_in_team(db, user_id, team_id)

    # 2 - админ, 3 - владелец
    # удалить может владелец, админ может удалять ниже админа
    if current_user_role.role is None:
        raise HTTPException(status_code=403, detail="You are not a member of this team.")

    if current_user_role.role <= 2 or (user_role == 2 and current_user_role.role != 3):
        raise HTTPException(status_code=403, detail="You do not have permission to remove users from this team.")

    if user_role is None:
        raise HTTPException(status_code=404, detail="User not found in this team.")
    
    if user_id == current_user.id:
        raise HTTPException(status_code=403, detail="You cannot remove yourself from this team.")
    
    await delete_user_from_team(db, user_role)
    
    return {"message": "User removed from team successfully"}


@router.put("/team/{team_id}/settings", summary="Изменение настроек команды")
async def update_team_settings(
    team_id: UUID,
    request: UpdateTeamSettingsRequest,
    current_user=Depends(get_current_user), 
    db: AsyncSession = Depends(get_db_session)
):
    """
    Изменяет настройки команды.

    Аргументы:
        team_id: Идентификатор команды.
        request: Тело запроса с новыми настройками.
        current_user: Текущий пользователь.
        db: Сессия базы данных.

    Возвращает:
        Сообщение об успешном изменении.
    """
    # Проверяем, что пользователь является владельцем команды
    user_role = await get_user_role_in_team(db, current_user.id, team_id)
    if user_role is None or user_role.role < 2:
        raise HTTPException(status_code=403, detail="You do not have permission to edit team settings.")

    team = await get_team(team_id, db)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    team.title = request.title
    await db.commit()
    return {"message": "Team settings updated successfully"}
