from typing import Protocol, Optional, Any, List

from fastapi import UploadFile


class IUoW(Protocol):
    ...

class IJWTService(Protocol):
    def encode_token(
        self,
        data: dict,
        expires_delta: Optional[int] = None,
        is_access_token: bool = True
    ) -> str: ...

    def decode_token(self, token: str) -> dict: ...


class IEmailService(Protocol):
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html: bool = False
    ) -> None: ...

class IHashService(Protocol):
    @staticmethod
    def hash_password(password: str) -> str: ...

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool: ...
