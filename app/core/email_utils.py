from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr

from app.core.config import settings

TEMPLATE_FOLDER = Path(__file__).parent.parent / "templates"
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    TEMPLATE_FOLDER=TEMPLATE_FOLDER,
)


class EmailUtils:
    @staticmethod
    async def send_email(
        email_to: EmailStr, subject: str, template_name: str, template_data: dict
    ):
        message = MessageSchema(
            subject=subject,
            recipients=[email_to],  # type: ignore
            template_body=template_data,
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name=template_name)
