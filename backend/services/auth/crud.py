from fastapi import APIRouter
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from .password import get_password_hash
from backend.web.api.v1.user.schema import UserCreate, UserUpdate
from backend.db.models.users import User, RefreshToken
from datetime import datetime, timedelta

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/auth")


async def create_user(db: AsyncSession, user_create: UserCreate, ip: str) -> User:
    """
    Создает нового пользователя в базе данных.

    :param db: сессия базы данных.
    :param user_create: схема создания пользователя.
    :param ip: IP-адрес, с которого зарегистрирован пользователь.
    :returns: созданный пользователь.
    """
    user = User(
        login=user_create.login,
        email=user_create.email,
        password=get_password_hash(user_create.password),
        last_login_ip=ip,
        last_login_dt=datetime.now(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User:
    """
    Получает пользователя по ID.

    :param db: сессия базы данных.
    :param user_id: идентификатор пользователя.
    :returns: найденный пользователь или None.
    """
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalar_one_or_none()

async def get_user_by_login(db: AsyncSession, login: str) -> User:
    """
    Получает пользователя по логину.

    :param db: сессия базы данных.
    :param login: логин пользователя.
    :returns: найденный пользователь или None.
    """
    result = await db.execute(select(User).filter(User.login == login))
    return result.scalar_one_or_none()

async def update_user(db: AsyncSession, user: User, user_update: UserUpdate) -> User:
    """
    Обновляет информацию о пользователе.

    :param db: сессия базы данных.
    :param user: пользователь, которого нужно обновить.
    :param user_update: схема обновления пользователя.
    :returns: обновленный пользователь.
    """
    for key, value in user_update.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return user

async def delete_user(db: AsyncSession, user: User) -> None:
    """
    Удаляет пользователя из базы данных.

    :param db: сессия базы данных.
    :param user: пользователь, которого нужно удалить.
    """
    await db.delete(user)
    await db.commit()


async def get_refresh_tokens_by_user_id(db: AsyncSession, user_id: int) -> list[RefreshToken]:
    """
    Возвращает список всех refresh токенов для указанного пользователя.

    :param db: сессия базы данных.
    :param user_id: идентификатор пользователя.
    :returns: список refresh токенов.
    """
    result = await db.execute(select(RefreshToken).filter(RefreshToken.user_id == user_id))
    return result.scalars().all()


async def delete_refresh_token_for_user(db: AsyncSession, user_id: int, token_value: str) -> None:
    """
    Удаляет определенный refresh токен для указанного пользователя.

    :param db: сессия базы данных.
    :param user_id: идентификатор пользователя.
    :param token_value: значение токена.
    """
    await db.execute(
        select(RefreshToken)
        .filter(RefreshToken.user_id == user_id, RefreshToken.value == token_value)
        .delete()
    )
    await db.commit()

async def get_active_refresh_token(db: AsyncSession, user_id: str) -> RefreshToken:
    """
    Возвращает активный refresh token по его значению.

    :param db: сессия базы данных.
    :param token_value: значение токена.
    :returns: объект RefreshToken или None, если токен не найден или не активен.
    """
    result = await db.execute(
        select(RefreshToken)
        .filter(RefreshToken.user_id == user_id)
    )
    refresh_token = result.scalars().first()
    if refresh_token:
        # Проверяем, не истек ли refresh token
        expiration_date = refresh_token.created_dt + timedelta(seconds=refresh_token.ttl_sec)
        if expiration_date > datetime.now():
            return refresh_token
        else:
            await delete_refresh_token_for_user(db, user_id, refresh_token.value)
    return None