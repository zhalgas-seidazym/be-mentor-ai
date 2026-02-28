from typing import Optional, Dict, List

from fastapi import HTTPException, status as s

from src.application.skills.dtos import SkillDTO
from src.application.skills.interfaces import ISkillController, ISkillSearchService, ISkillRepository
from src.application.users.interfaces import IUserSkillRepository
from src.application.users.dtos import UserSkillDTO
from src.domain.base_dto import PaginationDTO
from src.domain.interfaces import IUoW


class SkillController(ISkillController):
    def __init__(
            self,
            skill_repository: ISkillRepository,
            user_skill_repository: IUserSkillRepository,
            uow: IUoW,
            skill_search_service: ISkillSearchService,
    ):
        self._skill_repository = skill_repository
        self._user_skill_repository = user_skill_repository
        self._uow = uow
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

    async def create(self, name: str) -> SkillDTO:
        skill = await self._skill_repository.get_by_name(name)

        if skill:
            raise HTTPException(status_code=s.HTTP_409_CONFLICT, detail=f"Skill {name} already exists")

        async with self._uow:
            skill = await self._skill_repository.add(name)

        await self._skill_search_service.index(skill_id=skill.id, name=name)

        return skill

    async def get_my_skills(
        self,
        user_id: int,
        populate_skill: bool = False,
    ) -> List[UserSkillDTO]:
        res = await self._user_skill_repository.get_by_user_id(
            user_id=user_id,
            populate_skill=populate_skill,
            to_learn=False,
        )
        return res.items
