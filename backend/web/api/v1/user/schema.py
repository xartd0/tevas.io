from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

class UserCreate(BaseModel):
    """
    Схема для создания пользователя.
    
    Аргументы:
        first_name: Имя.
        last_name: Фамилия.
        login: Логин.
        email: Email.
        password: Пароль.
        team_id: Идентификатор команды.
    """
    first_name: str
    last_name: str
    login: str
    email: EmailStr
    password: str
    team_id: Optional[UUID] = None


class UserLogin(BaseModel):
    """
    Схема для авторизации пользователя.
    
    Аргументы:
        login: Логин.
        password: Пароль.
    """
    login: str
    password: str
         

class UserResponse(BaseModel):
    """
    Схема для создания пользователя.
    
    Аргументы:
        login: Логин.
        email: Email.
        team_id: Идентификатор команды.
    """
    login: str
    email: EmailStr
    team_id: Optional[UUID]

    class Config:
        from_attributes = True  


class UserUpdate(BaseModel):
    """
    Схема для обновления данных пользователя.
    
    Аргументы:
        login: Логин.
        email: Email.
        password: Новый пароль.
        current_password: Старый пароль.
        first_name: Имя.
        last_name: Фамилия.
    """
    login: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    current_password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserResponse(BaseModel):
    """
    Схема для ответа с данными пользователя.
    
    Аргументы:
        id: Идентификатор.
        login: Логин.
        email: Email.
        status_id: Статус.
        last_login_ip: IP последнего входа.
        last_login_dt: Дата последнего входа.
        first_name: Имя.
        last_name: Фамилия.
        created_dt: Дата создания.
        updated_dt: Дата обновления.
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
    """
    Схема для верификации.
    
    Аргументы:
        code: Код.
    """
    code: str


class UpdateAppearance(BaseModel):
    """
    Схема для изменения темы и цвета.
    """
    theme_is_light: bool
    main_color_hex: Optional[str] = None


class EmailResetPassword(BaseModel):
    """
    Схема для восстановления пароля по email.
    """
    email: EmailStr


class RestDataRequest(BaseModel):
    """
    Схема для восстановления пароля по email.
    """
    code: str
    new_password: str