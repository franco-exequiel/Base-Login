import smtplib
from email.message import EmailMessage

from app.core.config import settings


def send_email(recipient: str, subject: str, body: str) -> None:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.mail_from or settings.mail_username
    message["To"] = recipient
    message.set_content(body)
    with smtplib.SMTP(settings.mail_host, settings.mail_port, timeout=20) as smtp:
        if settings.mail_starttls:
            smtp.starttls()
        if settings.mail_username:
            smtp.login(settings.mail_username, settings.clean_mail_password)
        smtp.send_message(message)


def send_verification_email(recipient: str, raw_token: str) -> None:
    send_email(
        recipient,
        "Verify your email",
        f"Verify your email by opening this link:\n{settings.frontend_url}/verify-email?token={raw_token}",
    )


def send_password_reset_email(recipient: str, raw_token: str) -> None:
    send_email(
        recipient,
        "Reset your password",
        f"Reset your password by opening this link:\n{settings.frontend_url}/reset-password?token={raw_token}",
    )
