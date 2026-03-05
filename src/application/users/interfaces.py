from abc import ABC, abstractmethod
from typing import Optional

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
