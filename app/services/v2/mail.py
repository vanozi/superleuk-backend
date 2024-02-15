from smtplib import SMTP

from app.config import get_fastapi_mail_config
from app.models.pydantic import EmailSchema
from fastapi import Depends
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

fm: ConnectionConfig = FastMail(get_fastapi_mail_config())


class Mailer:
    async def send_invitation_message(email: EmailSchema):
        message = MessageSchema(
            subject="Uitnoding voor Gebr. Vroege app",
            # List of recipients, as many as you can pass
            recipients=email.model_dump().get("recipient_addresses"),
            template_body=email.model_dump().get("body"),
            subtype=MessageType.html
        )
        await fm.send_message(message, template_name="invite_email.html")

    async def send_welcome_message(email: EmailSchema):
        message = MessageSchema(
            subject="Welkom!!",
            # List of recipients, as many as you can pass
            recipients=email.model_dump().get("recipient_addresses"),
            template_body=email.model_dump().get("body"),
            subtype=MessageType.html
        )
        await fm.send_message(message, template_name="account_activation_email.html")

    async def send_reset_password_message(email: EmailSchema):
        message = MessageSchema(
            subject="Password reset",
            # List of recipients, as many as you can pass
            recipients=email.model_dump().get("recipient_addresses"),
            template_body=email.model_dump().get("body"),
            subtype=MessageType.html
        )
        await fm.send_message(message, template_name="reset_password_email.html")
