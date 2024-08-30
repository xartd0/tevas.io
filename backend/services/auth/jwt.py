from datetime import datetime, timedelta

from jose import JWTError, jwt

from ..settings import settings


def create_access_token(user_id: int, expires_delta: timedelta = None) -> str:
    """
    Создает JWT токен доступа.

    :param user_id: идентификатор пользователя.
    :param expires_delta: время жизни токена.
    :returns: сгенерированный JWT токен.
    """
    to_encode = {"sub": user_id}
    expire = datetime.utcnow() + (
        expires_delta
        if expires_delta
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(user_id: int, expires_delta: timedelta = None) -> str:
    """
    Создает JWT токен обновления.

    :param user_id: идентификатор пользователя.
    :param expires_delta: время жизни токена.
    :returns: сгенерированный JWT токен обновления.
    """
    to_encode = {"sub": user_id}
    expire = datetime.utcnow() + (
        expires_delta
        if expires_delta
        else timedelta(days=settings.refresh_token_expire_days)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def verify_token(token: str) -> dict:
    """
    Верифицирует JWT токен и декодирует его данные.

    :param token: JWT токен для верификации.
    :returns: данные, декодированные из токена.
    :raises: JWTError, если токен недействителен.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        return payload
    except JWTError as e:
        raise JWTError(f"Token validation error: {e}")
