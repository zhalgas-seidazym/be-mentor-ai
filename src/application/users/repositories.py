from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.users.dtos import UserDTO
from src.application.users.interfaces import IUserRepository
from src.application.users.models import User
from src.application.users.mappers import orm_to_dto, dto_to_orm


class UserRepository(IUserRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    def _base_query(self):
        return select(User)

    async def _fetch_one(self, query) -> Optional[UserDTO]:
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()
        return orm_to_dto(row) if row else None

    async def get_by_id(self, user_id: int) -> Optional[UserDTO]:
        query = self._base_query().where(User.id == user_id)
        return await self._fetch_one(query)

    async def get_by_email(self, email: str) -> Optional[UserDTO]:
        query = self._base_query().where(User.email == email)
        return await self._fetch_one(query)

    async def add(self, dto: UserDTO) -> Optional[UserDTO]:
        row = dto_to_orm(dto)

        self._session.add(row)

        await self._session.flush()
        await self._session.refresh(row)

        return orm_to_dto(row)

    async def update(self, user_id: int, dto: UserDTO) -> Optional[UserDTO]:
        query = self._base_query().where(User.id == user_id)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return None

        row = dto_to_orm(dto, row)

        await self._session.flush()
        await self._session.refresh(row)

        return orm_to_dto(row)

    async def delete(self, user_id: int) -> bool:
        query = self._base_query().where(User.id == user_id)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return False

        await self._session.delete(row)
        return True