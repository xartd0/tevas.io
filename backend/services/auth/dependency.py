from fastapi import Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from ..db.dependencies import get_db_session
from ..db.models.user import User
from .jwt import verify_token


def get_current_user(
    token: str = Depends(),
    db: Session = Depends(get_db_session),
) -> User:
    """
    Возвращает текущего аутентифицированного пользователя на основе JWT токена.

    :param token: JWT токен, переданный в запросе.
    :param db: сессия базы данных.
    :returns: пользовательский объект текущего пользователя.
    :raises: HTTPException с кодом 401, если пользователь не найден или токен недействителен.
    """
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user
