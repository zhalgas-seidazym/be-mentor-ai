from typing import List, Optional

from src.application.modules.interfaces import IModuleController
from src.application.skills.dtos import UserSkillDTO
from src.application.skills.interfaces import IUserSkillRepository
from src.domain.base_dto import PaginationDTO


class ModuleController(IModuleController):
    def __init__(
        self,
        user_skill_repository: IUserSkillRepository,
    ):
        self._user_skill_repository = user_skill_repository

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
