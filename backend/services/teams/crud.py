from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, update
from backend.db.models.teams import Team, UserTeamLink, Invitation
from backend.web.api.v1.teams.schema import UpdateTeamRequest
from sqlalchemy import func
from backend.web.api.v1.teams.schema import TeamUserResponse
from typing import List
from uuid import UUID
import uuid
from datetime import datetime

async def create_team(title: str, user_id: UUID, session: AsyncSession) -> UUID:
    """
    Создание новой команды с добавлением создателя в UserTeamLink с ролью 3 (создатель).

    Аргументы:
    - title (str): Название команды.
    - user_id (UUID): Идентификатор пользователя, который создает команду.
    - session (AsyncSession): Сессия базы данных.

    Возвращает:
    - UUID: Идентификатор созданной команды.
    """
    new_team = Team(title=title)
    session.add(new_team)
    await session.commit()
    await session.refresh(new_team)

    # Добавляем запись о создателе в UserTeamLink с ролью 3
    creator_link = UserTeamLink(user_id=user_id, team_id=new_team.id, role=3)
    session.add(creator_link)
    await session.commit()
    
    return new_team.id

async def get_team(team_id: UUID, session: AsyncSession):
    """
    Получение информации о команде по идентификатору.

    Аргументы:
    - team_id (UUID): Идентификатор команды.
    - session (AsyncSession): Сессия базы данных.

    Возвращает:
    - dict: Данные о команде, пользователях и проектах.
    """
    result = await session.execute(select(Team).where(Team.id == team_id))
    team = result.scalars().first()
    if not team:
        return None

    # Получаем связанные данные о пользователях и проектах
    users = await session.execute(select(UserTeamLink).where(UserTeamLink.team_id == team_id))
    # projects = await session.execute(select(TeamProjectLink).where(TeamProjectLink.team_id == team_id))

    team_data = {
        "team_id": team.id,
        "title": team.title,
        "status_id": team.status_id,
        "created_dt": team.created_dt.isoformat(),
        "updated_dt": team.updated_dt.isoformat(),
        "users": [{"user_id": link.user_id, "role_id": link.role} for link in users.scalars()],
        # "projects": [{"project_id": link.project_id} for link in projects.scalars()]
    }
    return team_data

async def update_team(request: UpdateTeamRequest, user_id: UUID, session: AsyncSession):
    """
    Обновление данных команды, если текущий пользователь — админ (роль 2) или создатель (роль 3).

    Аргументы:
    - request (UpdateTeamRequest): Данные для обновления команды.
    - user_id (UUID): Идентификатор пользователя, который пытается обновить команду.
    - session (AsyncSession): Сессия базы данных.

    Возвращает:
    - dict: Обновленные данные команды, либо None, если команда не найдена.
    """
    # Проверка прав на редактирование (пользователь должен быть админом или создателем)
    user_link = await session.execute(select(UserTeamLink).where(UserTeamLink.team_id == request.team_id, UserTeamLink.user_id == user_id))
    user_role = user_link.scalars().first()
    
    if not user_role or user_role.role not in [2, 3]:
        raise HTTPException(status_code=403, detail="Permission denied")

    stmt = (
        update(Team).
        where(Team.id == request.team_id).
        values(title=request.title, status_id=request.status_id).
        returning(Team)
    )
    result = await session.execute(stmt)
    updated_team = result.scalars().first()

    if not updated_team:
        return None

    # Удаляем существующие связи с пользователями и проектами и добавляем новые
    await session.execute(delete(UserTeamLink).where(UserTeamLink.team_id == request.team_id))
    # await session.execute(delete(TeamProjectLink).where(TeamProjectLink.team_id == request.team_id))

    for user in request.users:
        user_link = UserTeamLink(user_id=user.user_id, team_id=request.team_id, role=user.role_id)
        session.add(user_link)

    # for project in request.projects:
    #     project_link = TeamProjectLink(project_id=project.project_id, team_id=request.team_id)
    #     session.add(project_link)

    await session.commit()
    return await get_team(request.team_id, session)

async def delete_team(team_id: UUID, user_id: UUID, session: AsyncSession) -> bool:
    """
    Удаление команды по идентификатору, если текущий пользователь — создатель (роль 3).

    Аргументы:
    - team_id (UUID): Идентификатор команды.
    - user_id (UUID): Идентификатор пользователя, который пытается удалить команду.
    - session (AsyncSession): Сессия базы данных.

    Возвращает:
    - bool: True, если команда успешно удалена, иначе False.
    """
    # Проверка прав на удаление (только создатель команды может удалять)
    user_link = await session.execute(select(UserTeamLink).where(UserTeamLink.team_id == team_id, UserTeamLink.user_id == user_id))
    user_role = user_link.scalars().first()

    if not user_role or user_role.role != 3:
        raise HTTPException(status_code=403, detail="Permission denied")

    stmt = delete(Team).where(Team.id == team_id)
    result = await session.execute(stmt)
    await session.commit()
    
    return result.rowcount > 0

async def get_teams_by_user_id(db: AsyncSession, user_id: UUID) -> List[TeamUserResponse]:
    """
    Получает список команд, в которых состоит пользователь, и возвращает данные в формате TeamUserResponse.

    :param db: Сессия базы данных.
    :param user_id: ID пользователя.
    :return: Список команд в формате TeamUserResponse.
    """

    # Запрос для получения всех команд, связанных с пользователем
    result = await db.execute(
        select(
            Team.id.label('team_id'),
            Team.title,
            Team.status_id,
            func.count(UserTeamLink.user_id).label('amount_of_users'),
            UserTeamLink.role.label('my_role_id'),
            Team.created_dt,
            Team.updated_dt
        )
        .join(UserTeamLink, UserTeamLink.team_id == Team.id)
        .filter(UserTeamLink.user_id == user_id)
        .group_by(Team.id, UserTeamLink.role)
    )

    teams = result.all()

    # Преобразуем результат в список объектов TeamUserResponse
    return [
        TeamUserResponse(
            team_id=team.team_id,
            title=team.title,
            status_id=team.status_id,
            amount_of_users=team.amount_of_users,
            my_role_id=team.my_role_id,
            created_dt=team.created_dt.isoformat(),
            updated_dt=team.updated_dt.isoformat()
        )
        for team in teams
    ]

async def get_user_role_in_team(db: AsyncSession, user_id: uuid.UUID, team_id: uuid.UUID) -> int:
    """
    Проверяет роль пользователя в команде.

    Аргументы:
        db: Сессия базы данных.
        user_id: Идентификатор пользователя (UUID).
        team_id: Идентификатор команды (UUID).

    Возвращает:
        Роль пользователя (int) или None, если пользователь не состоит в команде.
    """
    result = await db.execute(select(UserTeamLink.role).where(UserTeamLink.user_id == user_id, UserTeamLink.team_id == team_id))
    return result.scalar()


async def create_invitation(db: AsyncSession, team_id: UUID, role_id: int, inviting_user_id: UUID, ttl_sec: int) -> Invitation:
    """
    Создает новое приглашение в команду.

    Аргументы:
        db: Сессия базы данных.
        team_id: Идентификатор команды.
        role_id: Идентификатор роли.
        inviting_user_id: Идентификатор приглашающего пользователя.
        ttl_sec: Время жизни ссылки в секундах.

    Возвращает:
        Объект Invitation.

    Исключения:
        HTTPException: Если пользователь не в команде или его роль меньше 2.
    """
    # Создаем приглашение
    new_invitation = Invitation(
        team_id=team_id,
        role_id=role_id,
        inviting_user_id=inviting_user_id,
        ttl_sec=ttl_sec,
        created_dt=datetime.now()
    )
    db.add(new_invitation)
    await db.commit()
    await db.refresh(new_invitation)
    return new_invitation

async def get_invitation_by_id(db: AsyncSession, invitation_id: uuid.UUID) -> Invitation:
    """
    Получает приглашение по его идентификатору.

    Аргументы:
        db: Сессия базы данных.
        invitation_id: Уникальный идентификатор приглашения (UUID).

    Возвращает:
        Объект Invitation, если найдено, иначе None.
    """
    result = await db.execute(select(Invitation).where(Invitation.id == invitation_id))
    return result.scalars().first()

async def deactivate_invitation(db: AsyncSession, invitation: Invitation) -> None:
    """
    Деактивирует приглашение.

    Аргументы:
        db: Сессия базы данных.
        invitation: Объект Invitation, который нужно деактивировать.
    """
    invitation.is_active = False
    await db.commit()

async def add_user_to_team(db: AsyncSession, user_id: UUID, team_id: UUID, role_id: int) -> UserTeamLink:
    """
    Добавляет пользователя в команду.

    Аргументы:
        db: Сессия базы данных.
        user_id: Идентификатор пользователя (UUID).
        team_id: Идентификатор команды (UUID).
        role_id: Роль пользователя в команде (int).

    Возвращает:
        Объект UserTeamLink.
    """
    user_team_link = UserTeamLink(
        user_id=user_id,
        team_id=team_id,
        role=role_id
    )
    db.add(user_team_link)
    await db.commit()
    await db.refresh(user_team_link)
    return user_team_link

async def get_invitations_by_team(db: AsyncSession, team_id: UUID) -> list[Invitation]:
    """
    Возвращает список всех приглашений для указанной команды.

    Аргументы:
        db: Сессия базы данных.
        team_id: Идентификатор команды (UUID).

    Возвращает:
        Список объектов Invitation.
    """
    result = await db.execute(select(Invitation).where(Invitation.team_id == team_id))
    return result.scalars().all()

async def deactivate_invitation_by_id(db: AsyncSession, invitation_id: UUID) -> None:
    """
    Деактивирует приглашение по его идентификатору.

    Аргументы:
        db: Сессия базы данных.
        invitation_id: Идентификатор приглашения (UUID).
    """
    result = await db.execute(select(Invitation).where(Invitation.id == invitation_id))
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    # Деактивируем приглашение
    invitation.is_active = False
    await db.commit()

async def delete_invitation(db: AsyncSession, invitation_id: UUID) -> None:
    """
    Удаляет приглашение из базы данных.

    Аргументы:
        db: Сессия базы данных.
        invitation_id: Идентификатор приглашения (UUID).
    """
    result = await db.execute(select(Invitation).where(Invitation.id == invitation_id))
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    await db.delete(invitation)
    await db.commit()
