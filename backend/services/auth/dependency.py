from fastapi import Depends, HTTPException, status, Response, Request
from jose import JWTError
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.auth.jwt import create_access_token, verify_token

from backend.db.dependencies import get_db_session
from backend.db.models.users import User
from backend.services.auth.crud import get_user_by_id, get_active_refresh_token
from jose.exceptions import ExpiredSignatureError, JWTError, JWTClaimsError

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    response: Response = None
):
    
    verify = False
    if "verify" in request.url.path:
        verify = True
    print(verify)

    """
    Возвращает текущего аутентифицированного пользователя на основе JWT токена.

    :param request: объект запроса.
    :param db: сессия базы данных.
    :returns: пользовательский объект текущего пользователя.
    :raises: HTTPException с кодом 401, если пользователь не найден, токен недействителен или истек.
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No access token provided",
        )

    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials for this user",
            )
    except ExpiredSignatureError:
        # Если access token истек, попытаемся обновить его с помощью refresh token
        try:
            # Декодируем истекший токен, чтобы получить user_id
            payload = verify_token(token, False)
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials for this user",
                )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        user = await get_user_by_id(db, user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        refresh_token = await get_active_refresh_token(db, user.id)
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found or expired",
            )

        # Обновляем токен доступа
        new_access_token = create_access_token(user_id=user_id)
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            max_age=60,
            samesite="None",  # Для кросс-доменных запросов
            secure=False,  # Поставь True, если используешь HTTPS
        )

        
    except JWTClaimsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
        )
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
        
    if user.status_id == -1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is banned",
        )
    
    if user.status_id == 0 and not verify:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not verified",
        )

    return user