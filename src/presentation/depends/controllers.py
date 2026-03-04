from dependency_injector.wiring import inject, Provide
from fastapi import Depends

from app.container import Container
from src.application.directions.controllers import DirectionSalaryController
from src.application.directions.interfaces import (
    IDirectionSalaryController,
    IDirectionSearchService,
    IDirectionRepository,
    IDirectionStatisticsService,
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
from src.application.users.controllers import UserController
from src.application.users.interfaces import (
    IUserRepository,
    IEmailOtpService,
    IUserController,
    IHashService,
)
from src.application.interview.controllers import InterviewController
from src.application.interview.interfaces import IInterviewController, IInterviewSessionRepository, IInterviewQuestionRepository
from src.domain.interfaces import IJWTService, IUoW, IOpenAIService
from src.presentation.depends.repositories import *
from src.presentation.depends.session import get_uow


@inject
async def get_user_controller(
        user_repository: IUserRepository = Depends(get_user_repository),
        user_skill_repository: IUserSkillRepository = Depends(get_user_skill_repository),
        skill_repository: ISkillRepository = Depends(get_skill_repository),
        question_repository: IQuestionRepository = Depends(get_question_repository),
        direction_repository: IDirectionRepository = Depends(get_direction_repository),
        city_repository: ICityRepository = Depends(get_city_repository),
        openai_service: IOpenAIService = Depends(Provide[Container.openai_service]),
        email_otp_service: IEmailOtpService = Depends(Provide[Container.email_otp_service]),
        jwt_service: IJWTService = Depends(Provide[Container.jwt_service]),
        hash_service: IHashService = Depends(Provide[Container.hash_service]),
        uow: IUoW = Depends(get_uow)
) -> IUserController:
    return UserController(
        user_repository=user_repository,
        user_skill_repository=user_skill_repository,
        skill_repository=skill_repository,
        question_repository=question_repository,
        direction_repository=direction_repository,
        city_repository=city_repository,
        openai_service=openai_service,
        email_otp_service=email_otp_service,
        jwt_service=jwt_service,
        hash_service=hash_service,
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
) -> IQuestionController:
    return QuestionController(
        question_repository=question_repository,
        user_question_repository=user_question_repository,
    )

@inject
async def get_interview_controller(
        interview_session_repository: IInterviewSessionRepository = Depends(get_interview_session_repository),
        interview_question_repository: IInterviewQuestionRepository = Depends(get_interview_question_repository),
        question_repository: IQuestionRepository = Depends(get_question_repository),
        user_skill_repository: IUserSkillRepository = Depends(get_user_skill_repository),
        user_question_repository: IUserQuestionRepository = Depends(get_user_question_repository),
        openai_service: IOpenAIService = Depends(Provide[Container.openai_service]),
        uow: IUoW = Depends(get_uow),
) -> IInterviewController:
    return InterviewController(
        interview_session_repository=interview_session_repository,
        interview_question_repository=interview_question_repository,
        question_repository=question_repository,
        user_skill_repository=user_skill_repository,
        user_question_repository=user_question_repository,
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
