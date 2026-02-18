from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from src.application.users.dtos import UserDTO


class IUserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[UserDTO]: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[UserDTO]: ...

    @abstractmethod
    async def add(self, user_data: Dict[str, Any]) -> Optional[UserDTO]: ...

    @abstractmethod
    async def update(self, user_id: int, user_data: Dict[str, Any]) -> Optional[UserDTO]: ...

    @abstractmethod
    async def delete(self, user_id: int) -> Optional[bool]: ...

class IUserController(ABC):
    pass