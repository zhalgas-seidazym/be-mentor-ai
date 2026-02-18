import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from fastapi import HTTPException


class EmailService:
    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str, from_email: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email

    async def send_email(self, to_email: str, subject: str, body: str, html: bool = False):
        """Асинхронная отправка письма."""
        msg = MIMEMultipart("alternative")
        msg["From"] = self.from_email
        msg["To"] = to_email
        msg["Subject"] = subject

        mime_type = "html" if html else "plain"
        msg.attach(MIMEText(body, mime_type))

        try:
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                start_tls=True,
                username=self.username,
                password=self.password,
            )
        except aiosmtplib.SMTPException as e:
            raise HTTPException(status_code=500, detail=f"Email sending error: {e}")

