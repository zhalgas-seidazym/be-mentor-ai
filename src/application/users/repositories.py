from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.application.users.dtos import UserDTO, UserSkillDTO
from src.application.users.interfaces import IUserRepository, IUserSkillRepository
from src.application.users.models import User, UserSkill
from src.application.users.mappers import user_orm_to_dto, user_dto_to_orm, user_skill_dto_to_orm, user_skill_orm_to_dto
from src.domain.base_dto import PaginationDTO


class UserRepository(IUserRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    def _base_query(
            self,
            populate_city: bool = False,
            populate_skills: bool = False,
            populate_direction: bool = False,
    ):
        query = select(User)

        if populate_city:
            query = query.options(
                selectinload(User.city)
            )

        if populate_direction:
            query = query.options(
                selectinload(User.direction)
            )

        if populate_skills:
            query = query.options(
                selectinload(User.user_skills)
                .selectinload(UserSkill.skill)
            )

        return query

    async def _fetch_one(
            self,
            query,
            populate_city: bool,
            populate_skills: bool,
            populate_direction: bool,
    ) -> Optional[UserDTO]:

        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        return (
            user_orm_to_dto(
                row,
                populate_city=populate_city,
                populate_skills=populate_skills,
                populate_direction=populate_direction,
            )
            if row
            else None
        )

    async def get_by_id(
            self,
            user_id: int,
            populate_city: bool = False,
            populate_skills: bool = False,
            populate_direction: bool = False,
    ) -> Optional[UserDTO]:

        query = self._base_query(
            populate_city=populate_city,
            populate_skills=populate_skills,
            populate_direction=populate_direction,
        ).where(User.id == user_id)

        return await self._fetch_one(
            query,
            populate_city,
            populate_skills,
            populate_direction,
        )

    async def get_by_email(
            self,
            email: str,
            populate_city: bool = False,
            populate_skills: bool = False,
            populate_direction: bool = False,
    ) -> Optional[UserDTO]:

        query = self._base_query(
            populate_city=populate_city,
            populate_skills=populate_skills,
            populate_direction=populate_direction,
        ).where(User.email == email)

        return await self._fetch_one(
            query,
            populate_city,
            populate_skills,
            populate_direction,
        )

    async def add(self, dto: UserDTO) -> Optional[UserDTO]:
        row = user_dto_to_orm(dto)

        self._session.add(row)

        await self._session.flush()
        await self._session.refresh(row)

        return user_orm_to_dto(row)

    async def update(self, user_id: int, dto: UserDTO) -> Optional[UserDTO]:
        query = self._base_query().where(User.id == user_id)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return None

        row = user_dto_to_orm(dto, row)

        await self._session.flush()
        await self._session.refresh(row)

        return user_orm_to_dto(row)

    async def delete(self, user_id: int) -> bool:
        query = self._base_query().where(User.id == user_id)
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

        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await self._session.execute(count_query)
        total = count_result.scalar_one()

        if pagination is None:
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
