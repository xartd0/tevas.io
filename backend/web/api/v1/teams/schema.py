from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional

# Схемы для запросов и ответов
class UserRole(BaseModel):
    """
    Описание роли пользователя в команде.
    
    Аргументы:
        user_id: Идентификатор пользователя.
        role_id: Идентификатор роли.
    """
    user_id: UUID
    login: str
    role_id: int  # Роль в команде: 0 = чтение, 1 = редактирование, 2 = админ, 3 = создатель

class ProjectID(BaseModel):
    """
    Описание проекта в команде.
    
    Аргументы:
        project_id: Идентификатор проекта.
    """
    project_id: UUID

class CreateTeamRequest(BaseModel):
    """
    Схема для создания команды.
    
    Аргументы:
        title: Название команды.
    """
    title: str

class UpdateTeamRequest(BaseModel):
    """
    Схема для обновления команды.
    
    Аргументы:
        team_id: Идентификатор команды.
        title: Название команды.
        status_id: Статус команды.
        users: Список пользователей с ролями.
        # projects: Список проектов.
    """
    team_id: UUID
    title: str
    status_id: int
    users: List[UserRole]
    # projects: List[ProjectID]

class TeamResponse(BaseModel):
    """
    Ответ на получение команды.
    
    Аргументы:
        team_id: Идентификатор команды.
        title: Название команды.
        status_id: Статус команды.
        created_dt: Дата создания.
        updated_dt: Дата обновления.
        users: Список пользователей с ролями.
        # projects: Список проектов.
    """
    team_id: UUID
    title: str
    status_id: int
    created_dt: str
    updated_dt: str
    users: List[UserRole]
    # projects: List[dict]

class TeamUserResponse(BaseModel):
    """
    Ответ на получение команд, связанных с пользователем.
    
    Аргументы:
        team_id: Идентификатор команды.
        title: Название команды.
        status_id: Статус команды.
        amount_of_users: Количество пользователей.
        my_role_id: Моя роль.
        created_dt: Дата создания.
        updated_dt: Дата обновления.
    """
    team_id: UUID
    title: str
    status_id: int
    amount_of_users: int
    my_role_id: int
    created_dt: str
    updated_dt: str

    class Config:
        from_attributes = True  

class InvitationCreateRequest(BaseModel):
    """
    Схема для создания приглашения.
    
    Аргументы:
        team_id: Идентификатор команды.
        role_id: Идентификатор роли.
        ttl_sec: Время жизни ссылки в секундах.
    """
    team_id: UUID
    role_id: int
    ttl_sec: int

class InvitationCreateResponse(BaseModel):
    """
    Ответ на запрос о создании приглашения.
    
    Аргументы:
        invitation_id: Идентификатор приглашения.
        is_active: Статус активности.
        ttl_sec: Время жизни ссылки в секундах.
        user_accepted_count: Количество пользователей, принявших приглашение.
    """
    id: UUID
    is_active: bool
    ttl_sec: int
    users_accepted: int

    class Config:
        from_attributes = True  

class InvitationAcceptResponse(BaseModel):
    """
    Ответ на успешное принятие приглашения.
    
    Аргументы:
        message: Сообщение.
        team_id: Идентификатор команды.
        role_id: Идентификатор роли.
        user_accepted_count: Количество пользователей, принявших приглашение.
    """
    message: str
    team_id: UUID
    role_id: int
    user_accepted_count: int

    class Config:
        from_attributes = True  

class UpdateInvitationRequest(BaseModel):
    """
    Схема для обновления приглашения.

    Аргументы:
        ttl_sec: Новый срок действия ссылки (опционально).
        role_id: Новая роль для приглашения (опционально).
        is_active: Новый статус активности (опционально).
    """
    ttl_sec: int | None = None
    role_id: int | None = None
    is_active: bool | None = None

class DeactivateInvitationResponse(BaseModel):
    """
    Схема для ответа на запрос о деактивации приглашения.
    
    Аргументы:
        message: Сообщение о результате операции.
    """
    message: str


class UpdateUserRoleInTeamRequest(BaseModel):
    """
    Схема для обновления роли пользователя в команде.

    Аргументы:
        user_id: Идентификатор пользователя.
        role_id: Новый идентификатор роли.
    """
    team_id: UUID
    user_id: UUID
    role_id: int

class UpdateTeamSettingsRequest(BaseModel):
    """
    Схема для обновления настроек команды.

    Аргументы:
        title: Новое название команды.
    """
    title: str