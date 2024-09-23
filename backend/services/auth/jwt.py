from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError

from backend.settings import settings
from typing import Dict


def create_access_token(user_id: int, expires_delta: timedelta = None) -> str:
    """
    Создает JWT токен доступа.

    :param user_id: идентификатор пользователя.
    :param expires_delta: время жизни токена.
    :returns: сгенерированный JWT токен.
    """
    to_encode = {"sub": user_id}
    expire = datetime.now(timezone.utc) + (
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
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta
        else timedelta(days=expires_delta)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def verify_token(token: str, verify: bool = True) -> Dict[str, any]:
    """
    Верифицирует JWT токен и декодирует его данные.

    :param token: JWT токен для верификации.
    :returns: данные, декодированные из токена.
    :raises: ExpiredSignatureError, если токен истек.
    :raises: JWTError, если токен недействителен.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            options={"verify_exp": verify},
        )
        return payload
    except ExpiredSignatureError:
        raise ExpiredSignatureError("Token has expired")
    except JWTClaimsError as e:
        raise JWTError(f"Invalid token claims: {e}")
    except JWTError as e:
        raise JWTError(f"Invalid token: {e}")