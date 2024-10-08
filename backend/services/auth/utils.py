from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from backend.db.models.users import User, RefreshToken
from datetime import timedelta
from .jwt import create_refresh_token
from .crud import get_user_by_login, get_active_refresh_token, get_user_by_email, check_verification_code_exist
from .password import verify_password
from backend.settings import settings
import random
import string

async def authenticate_user(db: AsyncSession, login: str, password: str) -> int:
    """
    Аутентифицирует пользователя на основе его логина и пароля.

    :param db: сессия базы данных.
    :param username: логин или email пользователя.
    :param password: пароль пользователя.
    :returns: идентификатор пользователя, если аутентификация успешна.
    :raises: HTTPException, если аутентификация не удалась.
    """
    try:
        if "@" in login:
            user = await get_user_by_email(db, email=login)
        else:
            user = await get_user_by_login(db, login=login)
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred.",
        )
    
    if not user or not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return user



async def create_and_store_refresh_token(user_id: int, db: AsyncSession) -> str:
    """
    Создает и сохраняет refresh token в базе данных.

    :param user_id: идентификатор пользователя.
    :param db: сессия базы данных.
    :returns: сгенерированный refresh token.
    """
    expires_delta = timedelta(days=settings.refresh_token_expire_days)
    refresh_token_value = create_refresh_token(user_id, expires_delta)

    try:
        # Удаляем старый refresh token, если он существует
        old_token = await get_active_refresh_token(db, user_id)
        if old_token:
            await db.delete(old_token)
            await db.commit()

        # Создаем новый refresh token
        refresh_token = RefreshToken(
            value=refresh_token_value,
            user_id=user_id,
            ttl_sec=int(expires_delta.total_seconds()),
        )
        db.add(refresh_token)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store refresh token in the database.",
        )

    return refresh_token_value


async def generate_verification_code(db: AsyncSession, length=6) -> str:
    """
    Генерирует случайный код для верификации.

    :param length: Длина кода.
    :param db: сессия базы данных.
    :return: Сгенерированный код.
    """
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    if await check_verification_code_exist(db, code):
        return await generate_verification_code(length, db)
    return code


async def set_cookie_custom(access_token: str, response) -> bool:


    if settings.swagger_cookie: # Чтобы работала авторизация на Swagger
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
        )
    else:
        response.set_cookie(
            key="access_token",
            value=access_token,
            samesite="None",  # Для кросс-доменных запросов
            secure=False,  # Поставь True, если используешь HTTPS
        )

    return True
