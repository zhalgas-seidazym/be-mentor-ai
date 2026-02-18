from sqlalchemy.ext.asyncio import AsyncSession


class UoW:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type is None:
            await self._session.commit()
        else:
            await self._session.rollback()