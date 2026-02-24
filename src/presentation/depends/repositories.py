from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.locations.interfaces import ICountryRepository, ICityRepository
from src.application.locations.repositories import CountryRepository, CityRepository
from src.application.skills.interfaces import ISkillRepository
from src.application.skills.repositories import SkillRepository
from src.application.users.interfaces import IUserRepository
from src.application.users.repositories import UserRepository
from src.presentation.depends.session import get_session


async def get_user_repository(
        session: AsyncSession = Depends(get_session),
) -> IUserRepository:
    return UserRepository(session)

async def get_skill_repository(
        session: AsyncSession = Depends(get_session),
) -> ISkillRepository:
    return SkillRepository(session)

async def get_country_repository(
        session: AsyncSession = Depends(get_session),
) -> ICountryRepository:
    return CountryRepository(session)

async def get_city_repository(
        session: AsyncSession = Depends(get_session),
) -> ICityRepository:
    return CityRepository(session)