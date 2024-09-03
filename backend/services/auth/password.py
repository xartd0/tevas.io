from passlib.context import CryptContext

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