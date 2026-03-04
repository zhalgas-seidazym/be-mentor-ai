from typing import Optional

from fastapi import HTTPException, status as s

from src.application.modules.interfaces import IModuleController, IModuleStatisticsService
from src.application.modules.dtos import ModuleStatisticsDTO
from src.application.skills.dtos import UserSkillDTO
from src.application.skills.interfaces import IUserSkillRepository
from src.domain.base_dto import PaginationDTO


class ModuleController(IModuleController):
    def __init__(
        self,
        user_skill_repository: IUserSkillRepository,
        module_statistics_service: IModuleStatisticsService,
    ):
        self._user_skill_repository = user_skill_repository
        self._module_statistics_service = module_statistics_service

    async def get_my_modules(
        self,
        user_id: int,
        pagination: Optional[PaginationDTO[UserSkillDTO]] = None,
        populate_skill: bool = False,
    ) -> PaginationDTO[UserSkillDTO]:
        return await self._user_skill_repository.get_by_user_id(
            user_id=user_id,
            pagination=pagination,
            populate_skill=populate_skill,
            to_learn=True,
        )

    async def get_statistics(
        self,
        user_id: int,
        module_id: int,
    ) -> ModuleStatisticsDTO:
        modules = await self._user_skill_repository.get_by_user_id(
            user_id=user_id,
            to_learn=True,
        )
        if not modules.items or not any(m.skill_id == module_id for m in modules.items):
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=f"Module {module_id} not found")

        return await self._module_statistics_service.get_statistics(
            user_id=user_id,
            module_id=module_id,
        )
