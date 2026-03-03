from abc import ABC, abstractmethod
from typing import List, Optional

from src.application.users.dtos import UserSkillDTO
from src.domain.base_dto import PaginationDTO


class IModuleController(ABC):
    @abstractmethod
    async def get_my_modules(
        self,
        user_id: int,
        pagination: Optional[PaginationDTO[UserSkillDTO]] = None,
        populate_skill: bool = False,
    ) -> PaginationDTO[UserSkillDTO]: ...
