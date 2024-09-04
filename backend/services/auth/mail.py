import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.settings import settings

async def send_email(to_email: str, subject: str, body: str):
    """
    Отправляет email через сервер mailcow.

    :param to_email: Адрес получателя.
    :param subject: Тема письма.
    :param body: Текст письма.
    """
    msg = MIMEMultipart()
    msg['From'] = settings.EMAIL_FROM
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
        server.starttls()
        server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
        server.send_message(msg)

async def send_verification_email(to_email: str, code: str):
    """
    Отправляет письмо с кодом верификации.

    :param to_email: Адрес получателя.
    :param code: Код верификации.
    """
    subject = "Verification Code"
    body = f"Your verification code is: {code}"
    await send_email(to_email, subject, body)

async def send_reset_password_email(to_email: str, code: str):
    """
    Отправляет письмо с кодом для сброса пароля.

    :param to_email: Адрес получателя.
    :param code: Код для сброса пароля.
    """
    subject = "Password Reset Code"
    body = f"Your password reset code is: {code}"
    await send_email(to_email, subject, body)


