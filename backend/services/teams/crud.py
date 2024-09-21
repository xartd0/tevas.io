from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, update
from backend.db.models.teams import Team, UserTeamLink
from backend.web.api.v1.teams.schema import UpdateTeamRequest
from uuid import UUID

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
