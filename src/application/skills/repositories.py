from typing import Optional, Any, Dict

from sqlalchemy import select, insert, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.skills.dtos import SkillDTO, PaginationSkillDTO
from src.application.skills.interfaces import ISkillRepository
from src.application.skills.models import Skill


class SkillRepository(ISkillRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, skill_id: int) -> Optional[SkillDTO]:
        query = select(Skill).where(Skill.id == skill_id)
        result = await self._session.execute(query)
        orm = result.scalar_one_or_none()
        return SkillDTO.to_application(orm) if orm else None

    async def get_by_name(self, name: str) -> Optional[SkillDTO]:
        query = select(Skill).where(Skill.name == name)
        result = await self._session.execute(query)
        orm = result.scalar_one_or_none()
        return SkillDTO.to_application(orm) if orm else None

    async def get(
            self,
            name: Optional[str] = None,
            pagination: Optional[Dict[str, Any]] = None,
    ) -> PaginationSkillDTO:

        pagination = pagination or {}

        page = max(int(pagination.get("page", 1)), 1)
        per_page = max(int(pagination.get("per_page", 10)), 10)

        offset = (page - 1) * per_page

        # ---- base query ----
        query = select(Skill)

        # ---- filter by name ----
        if name:
            query = query.where(Skill.name.ilike(f"%{name}%"))

        # ---- total count ----
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self._session.execute(count_query)
        total = count_result.scalar_one()

        # ---- apply pagination ----
        query = query.offset(offset).limit(per_page)

        result = await self._session.execute(query)
        rows = result.scalars().all()

        items = [SkillDTO.to_application(row) for row in rows]

        return PaginationSkillDTO(
            page=page,
            per_page=per_page,
            total=total,
            items=items,
        )

    async def add(self, name: str) -> Optional[SkillDTO]:
        query = insert(Skill).values(name=name).returning(Skill)
        result = await self._session.execute(query)
        orm = result.scalar_one_or_none()
        return SkillDTO.to_application(orm) if orm else None

    async def update(
            self,
            skill_id: int,
            name: str,
    ) -> Optional[SkillDTO]:
        query = (
            update(Skill)
            .where(Skill.id == skill_id)
            .values(name=name)
            .returning(Skill)
        )

        result = await self._session.execute(query)
        orm = result.scalar_one_or_none()

        return SkillDTO.to_application(orm) if orm else None

    async def delete(self, skill_id: int) -> bool:
        query = delete(Skill).where(Skill.id == skill_id).returning(Skill.id)
        result = await self._session.execute(query)
        deleted_id = result.scalar_one_or_none()
        return deleted_id is not None
