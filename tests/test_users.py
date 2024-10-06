import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
from uuid import uuid4
from sqlalchemy import select

from backend.db.models.users import User, UserVerificationCode  # Ваши модели
from backend.services.auth.password import get_password_hash  # Хэширование пароля
from backend.services.auth.jwt import create_access_token  # Создание токена доступа
from backend.services.auth.utils import generate_verification_code
from backend.services.auth.mail import send_verification_email, send_reset_password_email
from unittest.mock import patch
import time
import sys

@pytest.mark.anyio
async def test_login_user_success(client: AsyncClient, dbsession: AsyncSession):
    """
    Тест успешной авторизации пользователя.

    Шаги:
    - Создаем тестового пользователя в базе данных.
    - Пытаемся авторизоваться с правильными учетными данными.
    - Ожидаем успешный ответ с сообщением об успешной авторизации.
    """
    # Создаем тестового пользователя
    user = User(
        id=uuid4(),
        login="testuser",
        first_name="Test",
        last_name="User",
        password=get_password_hash("testpassword"),
        email="testuser@example.com",
        status_id=0,
    )
    dbsession.add(user)
    await dbsession.commit()

    # Пытаемся авторизоваться
    login_data = {
        "login": "testuser",
        "password": "testpassword"
    }
    response = await client.post("/api/v1/user/auth", json=login_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Login successful"

@pytest.mark.anyio
async def test_login_user_invalid_credentials(client: AsyncClient):
    """
    Тест авторизации с неверными учетными данными.

    Шаги:
    - Пытаемся авторизоваться с несуществующим логином и паролем.
    - Ожидаем ответ 401 Unauthorized с сообщением об ошибке.
    """
    login_data = {
        "login": "wronguser",
        "password": "wrongpassword"
    }
    response = await client.post("/api/v1/user/auth", json=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid credentials"

@pytest.mark.anyio
async def test_get_current_user_info_success(client: AsyncClient, dbsession: AsyncSession):
    """
    Тест получения информации о текущем пользователе.

    Шаги:
    - Создаем тестового пользователя и авторизуемся.
    - Получаем токен доступа из куки.
    - Делаем запрос к маршруту /me с заголовком Cookie.
    - Ожидаем успешный ответ с данными пользователя.
    """
    # Создаем тестового пользователя
    user = User(
        id=uuid4(),
        login="testuser2",
        first_name="Test",
        last_name="User",
        password=get_password_hash("testpassword2"),
        email="testuser@example.com",
        status_id=1,
    )
    dbsession.add(user)
    await dbsession.commit()

    # Авторизуемся
    login_data = {
        "login": "testuser2",
        "password": "testpassword2"
    }
    response = await client.post("/api/v1/user/auth", json=login_data)
    assert response.status_code == status.HTTP_200_OK
    # Получаем токен доступа из куки
    access_token = response.cookies.get("access_token")
    assert access_token is not None

    print(f"access_token: {access_token}", file=sys.stderr)

    # Делаем запрос к /me
    headers = {
        "Cookie": f"access_token={access_token}"
    }
    response = await client.get("/api/v1/user/me", headers=headers) 

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["login"] == "testuser2"

@pytest.mark.anyio
async def test_get_current_user_info_unauthorized(client: AsyncClient):
    """
    Тест доступа к /me без авторизации.

    Шаги:
    - Пытаемся получить информацию о текущем пользователе без токена.
    - Ожидаем ответ 401 Unauthorized.
    """
    response = await client.get("/api/v1/user/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "No access token provided"

@pytest.mark.anyio
async def test_update_user_settings_login_success(client: AsyncClient, dbsession: AsyncSession):
    """
    Тест успешного обновления логина пользователя.

    Шаги:
    - Создаем тестового пользователя и авторизуемся.
    - Обновляем логин на новый уникальный.
    - Ожидаем успешный ответ с обновленным логином.
    """
    # Создаем тестового пользователя
    user = User(
        id=uuid4(),
        login="testuser3",
        first_name="Test",
        last_name="User",
        password=get_password_hash("testpassword3"),
        email="testuser@example.com",
        status_id=1,
    )
    dbsession.add(user)
    await dbsession.commit()

    # Авторизуемся
    login_data = {
        "login": "testuser3",
        "password": "testpassword3"
    }
    response = await client.post("/api/v1/user/auth", json=login_data)
    access_token = response.cookies.get("access_token")

    # Обновляем логин
    headers = {
        "Cookie": f"access_token={access_token}"
    }
    update_data = {
        "login": "updateduser3"
    }
    response = await client.patch("/api/v1/user/settings", json=update_data, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["login"] == "updateduser3"

@pytest.mark.anyio
async def test_update_user_settings_login_exists(client: AsyncClient, dbsession: AsyncSession):
    """
    Тест обновления логина на уже существующий.

    Шаги:
    - Создаем двух пользователей.
    - Авторизуемся под первым пользователем.
    - Пытаемся обновить логин на логин второго пользователя.
    - Ожидаем ответ 400 Bad Request с сообщением об ошибке.
    """
    # Создаем двух пользователей
    user1 = User(
        id=uuid4(),
        login="testuser4",
        password=get_password_hash("testpassword4"),
        email="testuser4@example.com",
        first_name="Test",
        last_name="User",
        status_id=1,
    )
    user2 = User(
        id=uuid4(),
        login="testuser5",
        password=get_password_hash("testpassword5"),
        email="testuser5@example.com",
        first_name="Test",
        last_name="User",
        status_id=1,
    )
    dbsession.add_all([user1, user2])
    await dbsession.commit()

    # Авторизуемся под первым пользователем
    login_data = {
        "login": "testuser4",
        "password": "testpassword4"
    }
    response = await client.post("/api/v1/user/auth", json=login_data)
    access_token = response.cookies.get("access_token")

    # Пытаемся обновить логин на логин второго пользователя
    headers = {
        "Cookie": f"access_token={access_token}"
    }
    update_data = {
        "login": "testuser5"
    }
    response = await client.patch("/api/v1/user/settings", json=update_data, headers=headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "User with this login already exists"

@pytest.mark.anyio
async def test_confirm_new_email_success(client: AsyncClient, dbsession: AsyncSession, mocker):
    """
    Тест успешного подтверждения нового email пользователя.

    Шаги:
    - Создаем тестового пользователя и авторизуемся.
    - Мокаем отправку email и генерацию кода.
    - Запрашиваем изменение email.
    - Подтверждаем новый email с корректным кодом.
    - Ожидаем успешный ответ.
    """
    # Создаем тестового пользователя
    user = User(
        id=uuid4(),
        login="testuser6",
        password=get_password_hash("testpassword6"),
        email="testuser6@example.com",
        first_name="Test",
        last_name="User",
        status_id=1, 
    )
    dbsession.add(user)
    await dbsession.commit()

    # Авторизуемся
    login_data = {
        "login": "testuser6",
        "password": "testpassword6"
    }
    response = await client.post("/api/v1/user/auth", json=login_data)
    access_token = response.cookies.get("access_token")

    # Запрашиваем изменение email
    headers = {
        "Cookie": f"access_token={access_token}"
    }
    update_data = {
        "email": "newemail@example.com"
    }
    response = await client.patch("/api/v1/user/settings", json=update_data, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Confirmation code sent to the new email. Update email by confirming the code."

    # Получаем код из бд вместо email :(
    result = await dbsession.execute(select(UserVerificationCode).where(UserVerificationCode.user_id == user.id, UserVerificationCode.email == update_data["email"]))
    verification_code = result.scalar_one_or_none()
    assert verification_code is not None
    gen_code = verification_code.code

    # Подтверждаем новый email
    confirm_data = {
        "code": gen_code
    }
    response = await client.post("/api/v1/user/settings/email/confirm", json=confirm_data, headers=headers)
    print(response.json(), file=sys.stderr)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Email updated successfully"

@pytest.mark.anyio
async def test_verify_user_success(client: AsyncClient, dbsession: AsyncSession, mocker):
    """
    Тест успешной верификации пользователя.

    Шаги:
    - Создаем тестового пользователя и авторизуемся.
    - Мокаем отправку email и генерацию кода.
    - Запрашиваем отправку кода верификации.
    - Подтверждаем верификацию с корректным кодом.
    - Ожидаем успешный ответ.
    """
    # Создаем тестового пользователя
    user = User(
        id=uuid4(),
        login="testuser7",
        password=get_password_hash("testpassword7"),
        email="testuser7@example.com",
        first_name="Test",
        last_name="User",
        status_id=1, 
    )
    dbsession.add(user)
    await dbsession.commit()

    # Авторизуемся
    login_data = {
        "login": "testuser7",
        "password": "testpassword7"
    }
    response = await client.post("/api/v1/user/auth", json=login_data)
    access_token = response.cookies.get("access_token")

    # Запрашиваем отправку кода верификации
    headers = {
        "Cookie": f"access_token={access_token}"
    }
    response = await client.post("/api/v1/user/verify/send", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Verification code sent"

    # Получаем код из бд вместо email :(
    result = await dbsession.execute(select(UserVerificationCode).where(UserVerificationCode.user_id == user.id))
    verification_code = result.scalar_one_or_none()
    assert verification_code is not None
    gen_code = verification_code.code

    # Подтверждаем верификацию
    verify_data = {
        "code": gen_code
    }
    response = await client.post("/api/v1/user/verify", json=verify_data, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "User verified"

@pytest.mark.anyio
async def test_reset_password_success(client: AsyncClient, dbsession: AsyncSession, mocker):
    """
    Тест успешного сброса пароля.

    Шаги:
    - Создаем тестового пользователя.
    - Мокаем отправку email и генерацию кода.
    - Запрашиваем отправку кода сброса пароля.
    - Сбрасываем пароль с корректным кодом.
    - Ожидаем успешный ответ.
    """
    # Создаем тестового пользователя
    user = User(
        id=uuid4(),
        login="testuser8",
        password=get_password_hash("testpassword8"),
        email="testuser8@example.com",
        first_name="Test",
        last_name="User",
        status_id=1, 
    )
    dbsession.add(user)
    await dbsession.commit()


    # Запрашиваем отправку кода сброса пароля
    reset_data = {
        "email": "testuser8@example.com"
    }
    response = await client.post("/api/v1/user/password/reset/send", json=reset_data)
    print(response.json())
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Reset password code sent"

    # Получаем код из бд вместо email :(
    result = await dbsession.execute(select(UserVerificationCode).where(UserVerificationCode.user_id == user.id))
    verification_code = result.scalar_one_or_none()
    assert verification_code is not None
    gen_code = verification_code.code

    # Сбрасываем пароль
    reset_data = {
        "code": gen_code,
        "new_password": "newpassword8"
    }
    response = await client.post("/api/v1/user/password/reset", json=reset_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Password reset successful"

@pytest.mark.anyio
async def test_update_appearance_success(client: AsyncClient, dbsession: AsyncSession):
    """
    Тест успешного обновления настроек внешнего вида.

    Шаги:
    - Создаем тестового пользователя и авторизуемся.
    - Отправляем запрос на обновление темы и цвета.
    - Ожидаем успешный ответ с сообщением "Theme saved".
    """
    # Создаем тестового пользователя
    user = User(
        id=uuid4(),
        login="testuser9",
        password=get_password_hash("testpassword9"),
        email="testuser9@example.com",
        first_name="Test",
        last_name="User",
        status_id=1, 
    )
    dbsession.add(user)
    await dbsession.commit()

    # Авторизуемся
    login_data = {
        "login": "testuser9",
        "password": "testpassword9"
    }
    response = await client.post("/api/v1/user/auth", json=login_data)
    access_token = response.cookies.get("access_token")

    # Обновляем тему и цвет
    headers = {
        "Cookie": f"access_token={access_token}"
    }
    appearance_data = {
        "theme_is_light": True,
        "main_color_hex": "blue"
    }
    response = await client.patch("/api/v1/user/appearance", json=appearance_data, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Theme saved"
