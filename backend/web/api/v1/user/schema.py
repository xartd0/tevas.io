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

    class Config:
        from_attributes = True  

class UserLogin(BaseModel):
    """
    Модель для авторизации пользователя.
    """
    login: str
    password: str

    class Config:
        from_attributes = True  
         


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
    login: str

    class Config:
        from_attributes = True  


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
    created_dt: datetime
    updated_dt: datetime

    class Config:
        from_attributes = True  

