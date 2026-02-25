from typing import Optional

from fastapi import HTTPException, status as s

from src.application.skills.dtos import SkillDTO
from src.application.skills.interfaces import ISkillController, ISkillSearchService, ISkillRepository
from src.domain.base_dto import PaginationDTO


class SkillController(ISkillController):
    def __init__(
            self,
            skill_repository: ISkillRepository,
            skill_search_service: ISkillSearchService,
    ):
        self._skill_repository = skill_repository
        self._skill_search_service = skill_search_service

    async def skill_autocomplete(self, pagination: PaginationDTO[SkillDTO], q: Optional[str] = None) -> PaginationDTO[SkillDTO]:
        count = await self._skill_search_service.count()

        if count < 1:
            total = await self._skill_repository.get()
            total = total.total

            skills = await self._skill_repository.get(pagination=PaginationDTO[SkillDTO](per_page=total))
            skills = skills.items

            await self._skill_search_service.bulk_index(skills)

        res = await self._skill_search_service.search(pagination=pagination, name=q)
        return res

    async def get_by_id(self, skill_id: int) -> Optional[SkillDTO]:
        res = await self._skill_repository.get_by_id(skill_id)

        if res is None:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=f"Skill {skill_id} not found")

        return res