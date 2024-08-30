from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..db.models.user import User, RefreshToken

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Верифицирует, что предоставленный пароль совпадает с хешированным паролем.

    :param plain_password: предоставленный пользователем пароль.
    :param hashed_password: хешированный пароль из базы данных.
    :returns: True, если пароль совпадает, иначе False.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Хеширует предоставленный пароль.

    :param password: пароль, который нужно хешировать.
    :returns: хешированный пароль.
    """
    return pwd_context.hash(password)


def authenticate_user(db: Session, username: str, password: str) -> int:
    """
    Аутентифицирует пользователя на основе его логина и пароля.

    :param db: сессия базы данных.
    :param username: логин пользователя.
    :param password: пароль пользователя.
    :returns: идентификатор пользователя, если аутентификация успешна.
    :raises: HTTPException, если аутентификация не удалась.
    """
    user = db.query(User).filter(User.login == username).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return user.id


def create_and_store_refresh_token(user_id: int, db: Session) -> str:
    """
    Создает и сохраняет refresh token в базе данных.

    :param user_id: идентификатор пользователя.
    :param db: сессия базы данных.
    :returns: сгенерированный refresh token.
    """
    expires_delta = timedelta(days=30)  # Время жизни refresh токена
    refresh_token_value = create_refresh_token(user_id, expires_delta)

    # Сохраняем refresh token в базе данных
    refresh_token = RefreshToken(
        value=refresh_token_value,
        user_id=user_id,
        ttl_sec=int(expires_delta.total_seconds()),
    )
    db.add(refresh_token)
    db.commit()

    return refresh_token_value


def verify_refresh_token(refresh_token: str, db: Session) -> User:
    """
    Верифицирует refresh token и возвращает пользователя.

    :param refresh_token: JWT refresh token для верификации.
    :param db: сессия базы данных.
    :returns: пользовательский объект.
    :raises: HTTPException, если токен недействителен или не найден.
    """
    payload = verify_token(refresh_token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    # Проверяем, существует ли токен в базе данных и не истек ли он
    db_token = (
        db.query(RefreshToken)
        .filter(RefreshToken.value == refresh_token, RefreshToken.is_alive == True)
        .first()
    )
    if db_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user
