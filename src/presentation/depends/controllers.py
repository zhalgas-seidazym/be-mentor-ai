from dependency_injector.wiring import inject, Provide
from fastapi import Depends

from app.container import Container
from src.application.users.controllers import UserController
from src.application.users.interfaces import IUserRepository, IEmailOtpService, IUserController
from src.domain.interfaces import IJWTService, IHashService, IUoW
from src.presentation.depends.repositories import get_user_repository
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