from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse
from uuid import UUID

from backend.db.dependencies import get_db_session
from backend.services.auth.jwt import create_access_token
from backend.services.auth.utils import (
    authenticate_user,
    create_and_store_refresh_token,
)
from backend.web.api.v1.user.schema import UserCreate, UserResponse, UserUpdate
from backend.services.auth.crud import get_user_by_login, create_user, get_user_by_id
from backend.services.auth.dependency import get_current_user

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/auth")



@router.post("/auth")
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session),
    response: Response = Response()
):
    """
    Авторизация пользователя.

    :param form_data: форма с данными для авторизации (логин и пароль).
    :param db: сессия базы данных.
    :returns: JWT токены доступа и обновления.
    """
    user_id = await authenticate_user(db, form_data.username, form_data.password)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    access_token = create_access_token(user_id=str(user_id))
    await create_and_store_refresh_token(user_id=str(user_id), db=db)

    response.set_cookie(key="access_token", value=access_token, httponly=True)

    return {"message": "Login successful"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_user),
    response: Response = None  # Добавляем Response как зависимость
):

    return current_user

@router.put("/me", response_model=UserResponse)
async def update_user_settings(
    user_update: UserUpdate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Изменение настроек для текущего пользователя.

    :param user_update: схема обновления пользователя.
    :param current_user: текущий пользователь.
    :param db: сессия базы данных.
    :returns: обновленный пользователь.
    """
    return await update_user(db, current_user, user_update)

@router.get("/{id}", response_model=UserResponse)
async def get_user_info(
    request: Request,
    id: UUID, 
    db: AsyncSession = Depends(get_db_session),
):
    """
    Получение информации о пользователе по ID.

    :param id: идентификатор пользователя.
    :param db: сессия базы данных.
    :returns: данные пользователя.
    """
    user = get_user_by_id(db, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user



@router.post("", response_model=UserCreate, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_create: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Регистрация нового пользователя.

    :param user_create: схема для создания пользователя.
    :param db: сессия базы данных.
    :returns: созданный пользователь.
    :raises: HTTPException с кодом 400, если пользователь с таким логином или email уже существует.
    """
    ip = request.client.host 
    existing_user = await get_user_by_login(db, user_create.login)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this login already exists",
        )

    user = await create_user(db, user_create, ip)
    return user
