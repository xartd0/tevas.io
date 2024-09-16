from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

class UserCreate(BaseModel):
    """
    Модель для создания пользователя.
    """
    first_name: str
    last_name: str
    login: str
    email: EmailStr
    password: str
    team_id: Optional[UUID] = None


class UserLogin(BaseModel):
    """
    Модель для авторизации пользователя.
    """
    login: str
    password: str
         

class UserResponse(BaseModel):
    """
    Модель для создания пользователя.
    """
    login: str
    email: EmailStr
    team_id: Optional[UUID]

    class Config:
        from_attributes = True  


class UserUpdate(BaseModel):
    """
    Модель для обновления данных пользователя.
    """
    login: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    current_password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserResponse(BaseModel):
    """
    Модель для ответа с данными пользователя.
    """
    id: UUID
    login: str
    email: EmailStr
    status_id: int
    last_login_ip: Optional[str]
    last_login_dt: Optional[datetime]
    first_name: str
    last_name: str
    created_dt: datetime
    updated_dt: datetime

    class Config:
        from_attributes = True  


class VerificationCode(BaseModel):
    code: str