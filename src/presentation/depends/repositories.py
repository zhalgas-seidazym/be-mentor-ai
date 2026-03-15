from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.directions.interfaces import IDirectionRepository, ISalaryRepository
from src.application.directions.repositories import DirectionRepository, SalaryRepository
from src.application.locations.interfaces import ICountryRepository, ICityRepository
from src.application.locations.repositories import CountryRepository, CityRepository
from src.application.skills.interfaces import ISkillRepository, IUserSkillRepository
from src.application.skills.repositories import SkillRepository, UserSkillRepository
from src.application.users.interfaces import IUserRepository
from src.application.users.repositories import UserRepository
from src.application.questions.interfaces import IQuestionRepository, IUserQuestionRepository
from src.application.questions.repositories import QuestionRepository, UserQuestionRepository
from src.application.interview.interfaces import IInterviewSessionRepository, IInterviewQuestionRepository
from src.application.interview.repositories import InterviewSessionRepository, InterviewQuestionRepository
from src.application.learning_recommendations.interfaces import ILearningRecommendationRepository
from src.application.learning_recommendations.repositories import LearningRecommendationRepository
from src.application.vacancies.interfaces import IVacancyRepository, IVacancySkillRepository, IUserVacancyRepository
from src.application.vacancies.repositories import VacancyRepository, VacancySkillRepository, UserVacancyRepository
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

async def get_question_repository(
        session: AsyncSession = Depends(get_session),
) -> IQuestionRepository:
    return QuestionRepository(session)

async def get_user_question_repository(
        session: AsyncSession = Depends(get_session),
) -> IUserQuestionRepository:
    return UserQuestionRepository(session)

async def get_interview_session_repository(
        session: AsyncSession = Depends(get_session),
) -> IInterviewSessionRepository:
    return InterviewSessionRepository(session)

async def get_interview_question_repository(
        session: AsyncSession = Depends(get_session),
) -> IInterviewQuestionRepository:
    return InterviewQuestionRepository(session)

async def get_direction_repository(
        session: AsyncSession = Depends(get_session),
) -> IDirectionRepository:
    return DirectionRepository(session)

async def get_salary_repository(
        session: AsyncSession = Depends(get_session),
) -> ISalaryRepository:
    return SalaryRepository(session)

async def get_learning_recommendation_repository(
        session: AsyncSession = Depends(get_session),
) -> ILearningRecommendationRepository:
    return LearningRecommendationRepository(session)

async def get_vacancy_repository(
        session: AsyncSession = Depends(get_session),
) -> IVacancyRepository:
    return VacancyRepository(session)

async def get_vacancy_skill_repository(
        session: AsyncSession = Depends(get_session),
) -> IVacancySkillRepository:
    return VacancySkillRepository(session)

async def get_user_vacancy_repository(
        session: AsyncSession = Depends(get_session),
) -> IUserVacancyRepository:
    return UserVacancyRepository(session)
