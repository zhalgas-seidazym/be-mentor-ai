from dependency_injector.wiring import inject, Provide
from fastapi import Depends

from app.container import Container
from src.application.directions.controllers import DirectionSalaryController
from src.application.directions.interfaces import (
    IDirectionSalaryController,
    IDirectionSearchService,
    IDirectionRepository,
    IDirectionStatisticsService,
    ISalaryRepository,
)
from src.application.locations.controllers import LocationController
from src.application.modules.controllers import ModuleController
from src.application.modules.interfaces import IModuleController
from src.application.questions.controllers import QuestionController
from src.application.questions.interfaces import IQuestionRepository, IQuestionController, IUserQuestionRepository
from src.application.modules.interfaces import IModuleStatisticsService
from src.application.locations.interfaces import ICountryRepository, ICityRepository, ILocationController
from src.application.skills.controllers import SkillController
from src.application.skills.interfaces import ISkillRepository, ISkillController, ISkillSearchService, IUserSkillRepository
from src.application.users.auth.controllers import AuthController
from src.application.users.auth.interfaces import IAuthController, IEmailOtpService, IHashService, IOAuthService
from src.application.users.interfaces import IUserRepository
from src.application.users.user.controllers import UserController
from src.application.users.user.interfaces import IUserController, IUserService
from src.application.users.user.services import UserService
from src.application.interview.controllers import InterviewController
from src.application.interview.interfaces import IInterviewController, IInterviewSessionRepository, IInterviewQuestionRepository
from src.application.learning_recommendations.controllers import LearningRecommendationController
from src.application.learning_recommendations.interfaces import ILearningRecommendationController, ILearningRecommendationRepository
from src.application.vacancies.controllers import VacancyController
from src.application.vacancies.interfaces import (
    IVacancyController,
    IUserVacancyRepository,
    IVacancyRepository,
    IVacancySkillRepository,
)
from src.domain.interfaces import IJWTService, IUoW, IOpenAIService
from src.presentation.depends.repositories import *
from src.presentation.depends.session import get_uow
from src.infrastructure.integrations.airflow_client import AirflowClient
from redis.asyncio import Redis


@inject
async def get_auth_controller(
        user_repository: IUserRepository = Depends(get_user_repository),
        email_otp_service: IEmailOtpService = Depends(Provide[Container.email_otp_service]),
        oauth_service: IOAuthService = Depends(Provide[Container.oauth_service]),
        jwt_service: IJWTService = Depends(Provide[Container.jwt_service]),
        hash_service: IHashService = Depends(Provide[Container.hash_service]),
        airflow_client: AirflowClient = Depends(Provide[Container.airflow_client]),
        uow: IUoW = Depends(get_uow)
) -> IAuthController:
    return AuthController(
        user_repository=user_repository,
        email_otp_service=email_otp_service,
        oauth_service=oauth_service,
        jwt_service=jwt_service,
        hash_service=hash_service,
        airflow_client=airflow_client,
        uow=uow
    )

@inject
async def get_user_controller(
        user_repository: IUserRepository = Depends(get_user_repository),
        user_skill_repository: IUserSkillRepository = Depends(get_user_skill_repository),
        skill_repository: ISkillRepository = Depends(get_skill_repository),
        question_repository: IQuestionRepository = Depends(get_question_repository),
        direction_repository: IDirectionRepository = Depends(get_direction_repository),
        city_repository: ICityRepository = Depends(get_city_repository),
        salary_repository: ISalaryRepository = Depends(get_salary_repository),
        user_question_repository: IUserQuestionRepository = Depends(get_user_question_repository),
        interview_session_repository: IInterviewSessionRepository = Depends(get_interview_session_repository),
        interview_question_repository: IInterviewQuestionRepository = Depends(get_interview_question_repository),
        openai_service: IOpenAIService = Depends(Provide[Container.openai_service]),
        skill_search_service: ISkillSearchService = Depends(Provide[Container.skill_search_service]),
        hash_service: IHashService = Depends(Provide[Container.hash_service]),
        uow: IUoW = Depends(get_uow)
) -> IUserController:
    user_service: IUserService = UserService(
        user_repository=user_repository,
        user_skill_repository=user_skill_repository,
        skill_repository=skill_repository,
        question_repository=question_repository,
        user_question_repository=user_question_repository,
        interview_session_repository=interview_session_repository,
        interview_question_repository=interview_question_repository,
        salary_repository=salary_repository,
        city_repository=city_repository,
        direction_repository=direction_repository,
        openai_service=openai_service,
        skill_search_service=skill_search_service,
        uow=uow,
    )
    return UserController(
        user_repository=user_repository,
        skill_repository=skill_repository,
        direction_repository=direction_repository,
        salary_repository=salary_repository,
        city_repository=city_repository,
        hash_service=hash_service,
        user_service=user_service,
        uow=uow
    )

@inject
async def get_skill_controller(
        skill_repository: ISkillRepository = Depends(get_skill_repository),
        user_skill_repository: IUserSkillRepository = Depends(get_user_skill_repository),
        skill_search_service: ISkillSearchService = Depends(Provide[Container.skill_search_service]),
        uow: IUoW = Depends(get_uow),
) -> ISkillController:
    return SkillController(
        skill_repository=skill_repository,
        user_skill_repository=user_skill_repository,
        skill_search_service=skill_search_service,
        uow=uow
    )

async def get_module_controller(
        user_skill_repository: IUserSkillRepository = Depends(get_user_skill_repository),
        question_repository: IQuestionRepository = Depends(get_question_repository),
        user_question_repository: IUserQuestionRepository = Depends(get_user_question_repository),
) -> IModuleController:
    module_statistics_service: IModuleStatisticsService = Container.module_statistics_service(
        question_repository=question_repository,
        user_question_repository=user_question_repository,
    )
    return ModuleController(
        user_skill_repository=user_skill_repository,
        module_statistics_service=module_statistics_service,
    )

async def get_question_controller(
        question_repository: IQuestionRepository = Depends(get_question_repository),
        user_question_repository: IUserQuestionRepository = Depends(get_user_question_repository),
        skill_repository: ISkillRepository = Depends(get_skill_repository),
        user_skill_repository: IUserSkillRepository = Depends(get_user_skill_repository),
) -> IQuestionController:
    return QuestionController(
        question_repository=question_repository,
        user_question_repository=user_question_repository,
        skill_repository=skill_repository,
        user_skill_repository=user_skill_repository,
    )

@inject
async def get_interview_controller(
        interview_session_repository: IInterviewSessionRepository = Depends(get_interview_session_repository),
        interview_question_repository: IInterviewQuestionRepository = Depends(get_interview_question_repository),
        question_repository: IQuestionRepository = Depends(get_question_repository),
        user_skill_repository: IUserSkillRepository = Depends(get_user_skill_repository),
        user_question_repository: IUserQuestionRepository = Depends(get_user_question_repository),
        user_repository: IUserRepository = Depends(get_user_repository),
        openai_service: IOpenAIService = Depends(Provide[Container.openai_service]),
        uow: IUoW = Depends(get_uow),
) -> IInterviewController:
    return InterviewController(
        interview_session_repository=interview_session_repository,
        interview_question_repository=interview_question_repository,
        question_repository=question_repository,
        user_skill_repository=user_skill_repository,
        user_question_repository=user_question_repository,
        user_repository=user_repository,
        openai_service=openai_service,
        uow=uow,
    )

@inject
async def get_learning_recommendation_controller(
        learning_recommendation_repository: ILearningRecommendationRepository = Depends(
            get_learning_recommendation_repository
        ),
        skill_repository: ISkillRepository = Depends(get_skill_repository),
        user_skill_repository: IUserSkillRepository = Depends(get_user_skill_repository),
        openai_service: IOpenAIService = Depends(Provide[Container.openai_service]),
        uow: IUoW = Depends(get_uow),
) -> ILearningRecommendationController:
    return LearningRecommendationController(
        learning_recommendation_repository=learning_recommendation_repository,
        skill_repository=skill_repository,
        user_skill_repository=user_skill_repository,
        openai_service=openai_service,
        uow=uow,
    )

async def get_location_controller(
        country_repository: ICountryRepository = Depends(get_country_repository),
        city_repository: ICityRepository = Depends(get_city_repository)
) -> ILocationController:
    return LocationController(
        country_repository=country_repository,
        city_repository=city_repository,
    )

@inject
async def get_vacancy_controller(
        vacancy_repository: IVacancyRepository = Depends(get_vacancy_repository),
        vacancy_skill_repository: IVacancySkillRepository = Depends(get_vacancy_skill_repository),
        user_vacancy_repository: IUserVacancyRepository = Depends(get_user_vacancy_repository),
        airflow_client: AirflowClient = Depends(Provide[Container.airflow_client]),
        redis: Redis = Depends(Provide[Container.redis]),
) -> IVacancyController:
    return VacancyController(
        vacancy_repository=vacancy_repository,
        vacancy_skill_repository=vacancy_skill_repository,
        user_vacancy_repository=user_vacancy_repository,
        airflow_client=airflow_client,
        redis=redis,
    )

@inject
async def get_direction_salary_controller(
        salary_repository: ISalaryRepository = Depends(get_salary_repository),
        direction_repository: IDirectionRepository = Depends(get_direction_repository),
        city_repository: ICityRepository = Depends(get_city_repository),
        uow: IUoW = Depends(get_uow),
        openai_service: IOpenAIService = Depends(Provide[Container.openai_service]),
        direction_search_service: IDirectionSearchService = Depends(Provide[Container.direction_search_service]),
        user_skill_repository: IUserSkillRepository = Depends(get_user_skill_repository),
        question_repository: IQuestionRepository = Depends(get_question_repository),
        user_question_repository: IUserQuestionRepository = Depends(get_user_question_repository),
) -> IDirectionSalaryController:
    module_statistics_service: IModuleStatisticsService = Container.module_statistics_service(
        question_repository=question_repository,
        user_question_repository=user_question_repository,
    )
    direction_statistics_service: IDirectionStatisticsService = Container.direction_statistics_service(
        module_statistics_service=module_statistics_service,
        user_skill_repository=user_skill_repository,
    )
    return DirectionSalaryController(
        salary_repository=salary_repository,
        direction_repository=direction_repository,
        city_repository=city_repository,
        uow=uow,
        openai_service=openai_service,
        direction_search_service=direction_search_service,
        direction_statistics_service=direction_statistics_service,
    )
