from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Protocol

from src.application.users.dtos import UserDTO


class IUserRepository(ABC):

    @abstractmethod
    async def get_by_id(
        self,
        user_id: int,
        populate_city: bool = False,
        populate_skills: bool = False,
        populate_direction: bool = False,
    ) -> Optional[UserDTO]: ...

    @abstractmethod
    async def get_by_email(
        self,
        email: str,
        populate_city: bool = False,
        populate_skills: bool = False,
        populate_direction: bool = False,
    ) -> Optional[UserDTO]: ...

    @abstractmethod
    async def add(self, dto: UserDTO) -> Optional[UserDTO]: ...

    @abstractmethod
    async def update(
        self,
        user_id: int,
        dto: UserDTO,
    ) -> Optional[UserDTO]: ...

    @abstractmethod
    async def delete(self, user_id: int) -> bool: ...

class IUserController(ABC):
    @abstractmethod
    async def send_otp(self, email: str) -> Dict: ...

    @abstractmethod
    async def verify_otp_and_register(self, user_data: UserDTO, code: str) -> Dict: ...

    @abstractmethod
    async def login(self, user_data: UserDTO) -> Dict: ...

    @abstractmethod
    async def verify_otp_and_password_token(self, user_data: UserDTO, code: str) -> Dict: ...

    @abstractmethod
    async def reset_password(self, user_data: UserDTO) -> Dict: ...

    @abstractmethod
    async def refresh_token(self, user_data: UserDTO) -> Dict: ...

    @abstractmethod
    async def create_profile(
        self,
        user_id: int,
        name: str,
        city_id: int,
        direction_id: int,
        skill_ids: list[int],
        timezone: str,
    ) -> UserDTO: ...

    @abstractmethod
    async def get_profile(
        self,
        user_id: int,
        populate_city: bool = False,
        populate_direction: bool = False,
        populate_skills: bool = False,
    ) -> UserDTO: ...

    @abstractmethod
    async def get_profile_streak(self, user_id: int) -> Dict[str, Any]: ...

    @abstractmethod
    async def update_profile(
        self,
        user_id: int,
        name: Optional[str] = None,
        city_id: Optional[int] = None,
        password: Optional[str] = None,
        new_password: Optional[str] = None,
    ) -> UserDTO: ...

    @abstractmethod
    async def delete_user(self, user_id: int) -> Dict: ...

class IEmailOtpService(Protocol):
    async def send_otp(self, email: str, ttl: Optional[int] = None) -> None: ...

    async def verify_otp(self, email: str, code: str) -> None: ...

class IHashService(Protocol):
    @staticmethod
    def hash_password(password: str) -> str: ...

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool: ...
