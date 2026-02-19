from typing import Optional

from src.application.skills.dtos import PaginationSkillDTO
from src.application.skills.interfaces import ISkillController, ISkillSearchService, ISkillRepository


class SkillController(ISkillController):
    def __init__(
            self,
            skill_repository: ISkillRepository,
            skill_search_service: ISkillSearchService,
    ):
        self._skill_repository = skill_repository
        self._skill_search_service = skill_search_service

    async def skill_autocomplete(self, pagination: PaginationSkillDTO, q: Optional[str] = None) -> PaginationSkillDTO:
        count = await self._skill_search_service.count()

        if count < 1:
            total = await self._skill_repository.get()
            total = total.total

            skills = await self._skill_repository.get(pagination=PaginationSkillDTO(per_page=total).to_payload(exclude_none=True))
            skills = skills.items

            await self._skill_search_service.bulk_index(skills)

        res = await self._skill_search_service.search(pagination=pagination.to_payload(exclude_none=True), name=q)
        return res