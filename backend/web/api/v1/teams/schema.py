from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional

# Схемы для запросов и ответов
class UserRole(BaseModel):
    user_id: UUID
    role_id: int  # Роль в команде: 0 = чтение, 1 = редактирование, 2 = админ, 3 = создатель

class ProjectID(BaseModel):
    project_id: UUID

class CreateTeamRequest(BaseModel):
    title: str

class UpdateTeamRequest(BaseModel):
    team_id: UUID
    title: str
    status_id: int
    users: List[UserRole]
    # projects: List[ProjectID]

class TeamResponse(BaseModel):
    team_id: UUID
    title: str
    status_id: int
    created_dt: str
    updated_dt: str
    users: List[UserRole]
    # projects: List[dict]
