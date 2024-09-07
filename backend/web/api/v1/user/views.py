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
from backend.web.api.v1.user.schema import UserCreate, UserResponse, UserUpdate, UserLogin, VerificationCode
from backend.services.auth.crud import (
    get_user_by_login,
    create_user,
    get_user_by_id,
    get_verification_code,
    create_verification_code,
    update_user_status,
    update_user_password,
    get_user_by_email,
    get_user_by_code
)
from backend.services.auth.dependency import get_current_user
from backend.services.auth.mail import send_reset_password_email, send_verification_email
from backend.services.auth.utils import generate_verification_code
from datetime import datetime

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/auth")



@router.post("/auth")
async def login_user(
    form_data: UserLogin,
    db: AsyncSession = Depends(get_db_session),
    response: Response = Response()
):
    """
    Авторизация пользователя.

    :param form_data: форма с данными для авторизации (логин и пароль).
    :param db: сессия базы данных.
    :returns: JWT токены доступа и обновления.
    """
    user = await authenticate_user(db, form_data.login, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    user.last_login_dt = datetime.now()
    await db.commit()

    access_token = create_access_token(user_id=str(user.id))
    await create_and_store_refresh_token(user_id=str(user.id), db=db)

    response.set_cookie(key="access_token", value=access_token, httponly=True)

    return {"message": "Login successful"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_user),
    response: Response = None  # Добавляем Response как зависимость
):

    return current_user


@router.get("/{id}", response_model=UserResponse)
async def get_user_info(
    id: UUID, 
    db: AsyncSession = Depends(get_db_session),
):
    """
    Получение информации о пользователе по ID.

    :param id: идентификатор пользователя.
    :param db: сессия базы данных.
    :returns: данные пользователя.
    """
    user = await get_user_by_id(db, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/settings")
async def update_user_settings(
    user_update: UserUpdate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Обновление настроек пользователя.

    Позволяет пользователю изменить логин, email или пароль.
    Для изменения email и пароля требуется подтверждение.

    :param user_update: схема с данными для обновления пользователя.
    :param current_user: текущий авторизованный пользователь.
    :param db: сессия базы данных.
    :returns: обновленные данные пользователя.
    """
    # Check if the login is being updated and if it is unique
    if user_update.login and user_update.login != current_user.login:
        existing_user = await get_user_by_login(db, user_update.login)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this login already exists",
            )
        current_user.login = user_update.login

    # Update email with confirmation
    if user_update.email and user_update.email != current_user.email:
        existing_user = await get_user_by_email(db, user_update.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )
        # Send confirmation code to new email
        code = await generate_verification_code(db=db)
        await create_verification_code(db, current_user.id, code, email=user_update.email)
        await send_verification_email(user_update.email, code)

        # Email is updated only after confirmation, we return message for that.
        return {"message": "Confirmation code sent to the new email. Update email by confirming the code."}

    # Update password with confirmation
    if user_update.password and user_update.current_password:
        # Authenticate the current password
        user_id = await authenticate_user(db, current_user.login, user_update.current_password)
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid current password",
            )

        # Update password
        await update_user_password(db, current_user, user_update.password)


    # Update first_name and last_name
    if user_update.first_name and user_update.first_name != current_user.first_name:
        current_user.first_name = user_update.first_name

    if user_update.last_name and user_update.last_name != current_user.last_name:
        current_user.last_name = user_update.last_name

    # Persist other changes (like login)
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)

    return current_user


@router.post("/settings/email/confirm")
async def confirm_new_email(
    code: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Подтверждение нового email пользователя.

    :param code: код подтверждения, отправленный на новый email.
    :param current_user: текущий авторизованный пользователь.
    :param db: сессия базы данных.
    :returns: сообщение об успешной верификации.
    :raises: HTTPException с кодом 400, если код неверен или истек.
    """
    # Проверка верификационного кода
    verification_code = await get_verification_code(db, current_user.id, code)
    if not verification_code:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")

    # Обновление email пользователя
    current_user.email = verification_code.email  # предполагаем, что код хранит новый email
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)

    return {"message": "Email updated successfully"}


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



@router.post("/verify/send")
async def send_verification_code(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Отправляет код верификации на email текущего пользователя.
    """
    code = await generate_verification_code(db=db)
    await create_verification_code(db, current_user.id, code)
    await send_verification_email(current_user.email, code)
    return {"message": "Verification code sent"}

@router.post("/verify")
async def verify_user(
    code: VerificationCode,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Подтверждает верификацию пользователя по коду.
    """
    verification_code = await get_verification_code(db, current_user.id, code.code)
    if not verification_code:
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    await update_user_status(db, current_user, status_id=1)
    return {"message": "User verified"}

@router.post("/password/reset/send")
async def send_reset_password_code(
    email: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Отправляет код для сброса пароля на email пользователя.
    """
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    code = await generate_verification_code(db=db)
    await create_verification_code(db, user.id, code)
    await send_reset_password_email(user.email, code)
    return {"message": "Reset password code sent"}

@router.post("/password/reset")
async def reset_password(
    code: str,
    new_password: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Сбрасывает пароль пользователя по коду.
    """

    user = await get_user_by_code(db, code)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    reset_code = await get_verification_code(db, user.id, code)
    if not reset_code:
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    await update_user_password(db, user, new_password)
    return {"message": "Password reset successful"}
