from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.skills.dtos import SkillDTO
from src.application.skills.interfaces import ISkillRepository
from src.application.skills.models import Skill
from src.application.skills.mappers import orm_to_dto, dto_to_orm
from src.domain.base_dto import PaginationDTO


class SkillRepository(ISkillRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def _fetch_one(self, query) -> Optional[SkillDTO]:
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()
        return orm_to_dto(row)

    async def get_by_id(self, skill_id: int) -> Optional[SkillDTO]:
        query = select(Skill).where(Skill.id == skill_id)
        return await self._fetch_one(query)

    async def get_by_name(self, name: str) -> Optional[SkillDTO]:
        query = select(Skill).where(Skill.name == name)
        return await self._fetch_one(query)

    async def get(
            self,
            name: Optional[str] = None,
            pagination: Optional[PaginationDTO[SkillDTO]] = None,
    ) -> PaginationDTO[SkillDTO]:

        pagination = pagination or PaginationDTO[SkillDTO]()

        page = max(pagination.page or 1, 1)
        per_page = max(pagination.per_page or 10, 1)
        offset = (page - 1) * per_page

        base_query = select(Skill)

        if name:
            base_query = base_query.where(Skill.name.ilike(f"%{name}%"))

        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await self._session.execute(count_query)
        total = count_result.scalar_one()

        query = base_query.offset(offset).limit(per_page)
        result = await self._session.execute(query)
        rows = result.scalars().all()

        items = [orm_to_dto(row) for row in rows]

        return PaginationDTO[SkillDTO](
            page=page,
            per_page=per_page,
            total=total,
            items=items,
        )

    async def add(self, dto: SkillDTO) -> Optional[SkillDTO]:
        row = dto_to_orm(dto)

        self._session.add(row)

        await self._session.flush()
        await self._session.refresh(row)

        return orm_to_dto(row)

    async def update(
        self,
        skill_id: int,
        dto: SkillDTO,
    ) -> Optional[SkillDTO]:

        query = select(Skill).where(Skill.id == skill_id)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return None

        row = dto_to_orm(dto, row)

        await self._session.flush()
        await self._session.refresh(row)

        return orm_to_dto(row)

    async def delete(self, skill_id: int) -> bool:
        query = select(Skill).where(Skill.id == skill_id)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return False

        await self._session.delete(row)
        return True