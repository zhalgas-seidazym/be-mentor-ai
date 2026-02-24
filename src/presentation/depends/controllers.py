from dependency_injector.wiring import inject, Provide
from fastapi import Depends

from app.container import Container
from src.application.locations.controllers import LocationController
from src.application.locations.interfaces import ICountryRepository, ICityRepository, ILocationController
from src.application.skills.controllers import SkillController
from src.application.skills.interfaces import ISkillRepository, ISkillController, ISkillSearchService
from src.application.users.controllers import UserController
from src.application.users.interfaces import IUserRepository, IEmailOtpService, IUserController, IHashService
from src.domain.interfaces import IJWTService, IUoW
from src.presentation.depends.repositories import get_user_repository, get_skill_repository, get_country_repository, \
    get_city_repository
from src.presentation.depends.session import get_uow


@inject
async def get_user_controller(
        user_repository: IUserRepository = Depends(get_user_repository),
        email_otp_service: IEmailOtpService = Depends(Provide[Container.email_otp_service]),
        jwt_service: IJWTService = Depends(Provide[Container.jwt_service]),
        hash_service: IHashService = Depends(Provide[Container.hash_service]),
        uow: IUoW = Depends(get_uow)
) -> IUserController:
    return UserController(
        user_repository=user_repository,
        email_otp_service=email_otp_service,
        jwt_service=jwt_service,
        hash_service=hash_service,
        uow=uow
    )

@inject
async def get_skill_controller(
        skill_repository: ISkillRepository = Depends(get_skill_repository),
        skill_search_service: ISkillSearchService = Depends(Provide[Container.skill_search_service]),
) -> ISkillController:
    return SkillController(
        skill_repository=skill_repository,
        skill_search_service=skill_search_service,
    )

# @inject
async def get_location_controller(
        country_repository: ICountryRepository = Depends(get_country_repository),
        city_repository: ICityRepository = Depends(get_city_repository)
) -> ILocationController:
    return LocationController(
        country_repository=country_repository,
        city_repository=city_repository,
    )