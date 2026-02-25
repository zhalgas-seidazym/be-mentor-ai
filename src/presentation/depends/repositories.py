from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.directions.interfaces import IDirectionRepository, ISalaryRepository
from src.application.directions.repositories import DirectionRepository, SalaryRepository
from src.application.locations.interfaces import ICountryRepository, ICityRepository
from src.application.locations.repositories import CountryRepository, CityRepository
from src.application.skills.interfaces import ISkillRepository
from src.application.skills.repositories import SkillRepository
from src.application.users.interfaces import IUserRepository, IUserSkillRepository
from src.application.users.repositories import UserRepository, UserSkillRepository
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

async def get_user_skill_repository(
        session: AsyncSession = Depends(get_session),
) -> IUserSkillRepository:
    return UserSkillRepository(session)

async def get_direction_repository(
        session: AsyncSession = Depends(get_session),
) -> IDirectionRepository:
    return DirectionRepository(session)

async def get_salary_repository(
        session: AsyncSession = Depends(get_session),
) -> ISalaryRepository:
    return SalaryRepository(session)