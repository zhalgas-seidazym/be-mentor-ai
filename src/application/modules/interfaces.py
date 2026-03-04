from abc import ABC, abstractmethod
from typing import Optional

from src.application.skills.dtos import UserSkillDTO
from src.domain.base_dto import PaginationDTO
from src.application.modules.dtos import ModuleStatisticsDTO


class IModuleStatisticsService(ABC):
    @abstractmethod
    async def get_statistics(
        self,
        user_id: int,
        module_id: int,
    ) -> ModuleStatisticsDTO: ...


class IModuleController(ABC):
    @abstractmethod
    async def get_my_modules(
        self,
        user_id: int,
        pagination: Optional[PaginationDTO[UserSkillDTO]] = None,
        populate_skill: bool = False,
    ) -> PaginationDTO[UserSkillDTO]: ...

    @abstractmethod
    async def get_statistics(
        self,
        user_id: int,
        module_id: int,
    ) -> ModuleStatisticsDTO: ...
