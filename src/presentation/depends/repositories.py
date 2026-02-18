from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.users.interfaces import IUserRepository
from src.application.users.repositories import UserRepository
from src.presentation.depends.session import get_session


async def get_user_repository(
        session: AsyncSession = Depends(get_session),
) -> IUserRepository:
    return UserRepository(session)