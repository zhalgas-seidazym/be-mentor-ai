from typing import Optional, Any, Dict

from sqlalchemy import select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.users.dtos import UserDTO
from src.application.users.interfaces import IUserRepository
from src.application.users.models import User


class UserRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: int) -> Optional[UserDTO]:
        query = select(User).where(User.id == user_id)
        result = await self._session.execute(query)
        orm = result.scalar_one_or_none()
        return UserDTO.to_application(orm) if orm else None

    async def get_by_email(self, email: str) -> Optional[UserDTO]:
        query = select(User).where(User.email == email)
        result = await self._session.execute(query)
        orm = result.scalar_one_or_none()
        return UserDTO.to_application(orm) if orm else None

    async def add(self, user_data: Dict[str, Any]) -> Optional[UserDTO]:
        query = insert(User).values(**user_data).returning(User)
        result = await self._session.execute(query)
        orm = result.scalar_one_or_none()
        return UserDTO.to_application(orm) if orm else None

    async def update(self, user_id: int, user_data: Dict[str, Any]) -> Optional[UserDTO]:
        if not user_data:
            return await self.get_by_id(user_id)

        query = (
            update(User)
            .where(User.id == user_id)
            .values(**user_data)
            .returning(User)
        )
        result = await self._session.execute(query)
        orm = result.scalar_one_or_none()
        return UserDTO.to_application(orm) if orm else None

    async def delete(self, user_id: int) -> Optional[bool]:
        query = delete(User).where(User.id == user_id).returning(User.id)
        result = await self._session.execute(query)
        delete_id = result.scalar_one_or_none()
        return delete_id is not None