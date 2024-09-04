from fastapi import APIRouter
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID
from .password import get_password_hash
from backend.web.api.v1.user.schema import UserCreate, UserUpdate
from backend.db.models.users import User, RefreshToken, UserVerificationCode
from datetime import datetime, timedelta
import uuid

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


async def get_user_by_email(db: AsyncSession, email: str) -> User:
    """
    Получает пользователя по email.

    :param db: Сессия базы данных.
    :param email: Email пользователя.
    :return: Объект User или None, если пользователь не найден.
    """
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()

async def create_verification_code(db: AsyncSession, user_id: uuid.UUID, code: str) -> UserVerificationCode:
    """
    Создает или обновляет код верификации для пользователя. 

    Если запись уже существует, она обновляется новым кодом и временем создания.
    Если запись не существует, создается новая запись.

    :param db: Сессия базы данных.
    :param user_id: ID пользователя.
    :param code: Код верификации.
    :return: Объект UserVerificationCode.
    """
    existing_code = await db.execute(
        select(UserVerificationCode).where(UserVerificationCode.user_id == user_id)
    )
    existing_code = existing_code.scalar_one_or_none()

    if existing_code:
        # Обновляем существующий код
        await db.execute(
            update(UserVerificationCode)
            .where(UserVerificationCode.user_id == user_id)
            .values(code=code)
        )
    else:
        # Создаем новую запись с кодом
        new_verification_code = UserVerificationCode(user_id=user_id, code=code)
        db.add(new_verification_code)

    await db.commit()

    # Возвращаем актуальный объект UserVerificationCode
    return existing_code if existing_code else new_verification_code

async def get_verification_code(db: AsyncSession, user_id: uuid.UUID, code: str) -> UserVerificationCode:
    """
    Получает код верификации по ID пользователя и коду.

    :param db: Сессия базы данных.
    :param user_id: ID пользователя.
    :param code: Код верификации.
    :return: Объект UserVerificationCode или None, если код не найден или истек.
    """
    expiration_time = datetime.now() - timedelta(minutes=15)
    result = await db.execute(
        select(UserVerificationCode)
        .filter(UserVerificationCode.user_id == user_id)
        .filter(UserVerificationCode.code == code)
        .filter(UserVerificationCode.created_at > expiration_time)
    )
    return result.scalar_one_or_none()

async def update_user_status(db: AsyncSession, user: User, status_id: int):
    """
    Обновляет статус пользователя.

    :param db: Сессия базы данных.
    :param user: Объект User.
    :param status_id: Новый статус пользователя.
    """
    user.status_id = status_id
    await db.commit()

async def update_user_password(db: AsyncSession, user: User, new_password: str):
    """
    Обновляет пароль пользователя.

    :param db: Сессия базы данных.
    :param user: Объект User.
    :param new_password: Новый пароль пользователя.
    """
    user.password = new_password  # Добавьте хэширование пароля, если нужно
    await db.commit()