from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.application.users.dtos import UserDTO
from src.application.users.interfaces import IUserRepository
from src.application.users.models import User, UserSkill
from src.application.users.mappers import user_orm_to_dto, user_dto_to_orm


class UserRepository(IUserRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    def _base_query(
            self,
            populate_city: bool = False,
            populate_skills: bool = False,
    ):
        query = select(User)

        if populate_city:
            query = query.options(
                selectinload(User.city)
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
    ) -> Optional[UserDTO]:

        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        return (
            user_orm_to_dto(
                row,
                populate_city=populate_city,
                populate_skills=populate_skills,
            )
            if row
            else None
        )

    async def get_by_id(
            self,
            user_id: int,
            populate_city: bool = False,
            populate_skills: bool = False,
    ) -> Optional[UserDTO]:

        query = self._base_query(
            populate_city=populate_city,
            populate_skills=populate_skills,
        ).where(User.id == user_id)

        return await self._fetch_one(
            query,
            populate_city,
            populate_skills,
        )

    async def get_by_email(
            self,
            email: str,
            populate_city: bool = False,
            populate_skills: bool = False,
    ) -> Optional[UserDTO]:

        query = self._base_query(
            populate_city=populate_city,
            populate_skills=populate_skills,
        ).where(User.email == email)

        return await self._fetch_one(
            query,
            populate_city,
            populate_skills,
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