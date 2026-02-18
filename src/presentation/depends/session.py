from typing import AsyncGenerator

from dependency_injector.wiring import inject, Provide
from fastapi import Depends
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.container import Container
from src.domain.interfaces import IUoW
from src.infrastructure.dbs.uow import UoW


@inject
async def get_session(
        session_factory: async_sessionmaker[AsyncSession] = Depends(
            Provide[Container.session_factory]
        ),
) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session

async def get_uow(session: AsyncSession = Depends(get_session)) -> IUoW:
    return UoW(session=session)