from abc import ABC, abstractmethod
from typing import Dict, Optional, Protocol

from src.application.users.dtos import UserDTO


class IAuthController(ABC):
    @abstractmethod
    async def send_otp(self, email: str) -> Dict: ...

    @abstractmethod
    async def verify_otp_and_register(self, user_data: UserDTO, code: str) -> Dict: ...

    @abstractmethod
    async def login(self, user_data: UserDTO) -> Dict: ...

    @abstractmethod
    async def oauth_start(self, provider: str) -> Dict: ...

    @abstractmethod
    async def oauth_callback(self, provider: str, code: str, state: str) -> Dict: ...

    @abstractmethod
    async def verify_otp_and_password_token(self, user_data: UserDTO, code: str) -> Dict: ...

    @abstractmethod
    async def reset_password(self, user_data: UserDTO) -> Dict: ...

    @abstractmethod
    async def refresh_token(self, user_data: UserDTO) -> Dict: ...


class IEmailOtpService(Protocol):
    async def send_otp(self, email: str, ttl: Optional[int] = None) -> None: ...

    async def verify_otp(self, email: str, code: str) -> None: ...


class IHashService(Protocol):
    @staticmethod
    def hash_password(password: str) -> str: ...

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool: ...


class IOAuthService(Protocol):
    async def build_authorization_url(self, provider: str) -> Dict[str, str]: ...

    async def exchange_code_for_email(self, provider: str, code: str, state: str) -> Dict[str, str]: ...
