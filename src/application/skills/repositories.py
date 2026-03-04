from typing import Optional, List

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.application.skills.dtos import SkillDTO, UserSkillDTO
from src.application.skills.interfaces import ISkillRepository, IUserSkillRepository
from src.application.skills.models import Skill, UserSkill
from src.application.skills.mappers import (
    skill_orm_to_dto,
    skill_dto_to_orm,
    user_skill_orm_to_dto,
    user_skill_dto_to_orm,
)
from src.domain.base_dto import PaginationDTO


class SkillRepository(ISkillRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    def _base_query(self):
        return select(Skill)

    async def _fetch_one(self, query) -> Optional[SkillDTO]:
        result = await self._session.execute(query)
        row = result.scalars().first()
        return skill_orm_to_dto(row) if row else None

    async def get_by_id(self, skill_id: int) -> Optional[SkillDTO]:
        query = self._base_query().where(Skill.id == skill_id)
        return await self._fetch_one(query)

    async def get_by_name(self, name: str) -> Optional[SkillDTO]:
        query = self._base_query().where(
            func.lower(Skill.name) == func.lower(name)
        )
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

        base_query = self._base_query()

        if name:
            base_query = base_query.where(
                Skill.name.ilike(f"%{name}%")
            )

        count_query = select(func.count()).select_from(
            base_query.subquery()
        )
        count_result = await self._session.execute(count_query)
        total = count_result.scalar_one()

        query = base_query.offset(offset).limit(per_page)
        result = await self._session.execute(query)
        rows = result.scalars().all()

        items: List[SkillDTO] = [
            skill_orm_to_dto(row) for row in rows
        ]

        return PaginationDTO[SkillDTO](
            page=page,
            per_page=per_page,
            total=total,
            items=items,
        )

    async def add(self, dto: SkillDTO) -> Optional[SkillDTO]:
        row = skill_dto_to_orm(dto)

        self._session.add(row)

        await self._session.flush()
        await self._session.refresh(row)

        return skill_orm_to_dto(row)

    async def update(
        self,
        skill_id: int,
        dto: SkillDTO,
    ) -> Optional[SkillDTO]:

        query = self._base_query().where(
            Skill.id == skill_id
        )
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return None

        row = skill_dto_to_orm(dto, row)

        await self._session.flush()
        await self._session.refresh(row)

        return skill_orm_to_dto(row)

    async def delete(self, skill_id: int) -> bool:
        query = self._base_query().where(
            Skill.id == skill_id
        )
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return False

        await self._session.delete(row)
        return True


class UserSkillRepository(IUserSkillRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    def _base_query(self, populate_skill: bool = False):
        query = select(UserSkill)

        if populate_skill:
            query = query.options(
                selectinload(UserSkill.skill)
            )

        return query

    async def get_by_user_id(
        self,
        user_id: int,
        pagination: Optional[PaginationDTO[UserSkillDTO]] = None,
        populate_skill: bool = False,
        to_learn: Optional[bool] = None,
    ) -> PaginationDTO[UserSkillDTO]:

        base_query = self._base_query(populate_skill).where(UserSkill.user_id == user_id)

        if to_learn is not None:
            base_query = base_query.where(UserSkill.to_learn == to_learn)
            if to_learn is True:
                base_query = base_query.order_by(desc(UserSkill.match_percentage))

        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await self._session.execute(count_query)
        total = count_result.scalar_one()

        if pagination is None or pagination.per_page is None:
            query = base_query
            page = 1
            per_page = total
        else:
            page = max(pagination.page or 1, 1)
            per_page = max(pagination.per_page or 10, 1)
            offset = (page - 1) * per_page
            query = base_query.offset(offset).limit(per_page)

        result = await self._session.execute(query)
        rows = result.scalars().all()

        items: List[UserSkillDTO] = [
            user_skill_orm_to_dto(row, populate_skill=populate_skill)
            for row in rows
        ]

        return PaginationDTO[UserSkillDTO](
            page=page,
            per_page=per_page,
            total=total,
            items=items,
        )

    async def add(self, dto: UserSkillDTO) -> Optional[UserSkillDTO]:
        row = user_skill_dto_to_orm(dto)

        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)

        return user_skill_orm_to_dto(row)

    async def update(
        self,
        user_id: int,
        skill_id: int,
        dto: UserSkillDTO,
    ) -> Optional[UserSkillDTO]:

        query = select(UserSkill).where(
            UserSkill.user_id == user_id,
            UserSkill.skill_id == skill_id,
        )

        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return None

        row = user_skill_dto_to_orm(dto, row)

        await self._session.flush()
        await self._session.refresh(row)

        return user_skill_orm_to_dto(row)

    async def delete(
        self,
        user_id: int,
        skill_id: int,
    ) -> bool:

        query = select(UserSkill).where(
            UserSkill.user_id == user_id,
            UserSkill.skill_id == skill_id,
        )

        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return False

        await self._session.delete(row)
        return True
