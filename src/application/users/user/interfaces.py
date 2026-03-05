from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from src.application.users.dtos import UserDTO


class IUserController(ABC):
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
