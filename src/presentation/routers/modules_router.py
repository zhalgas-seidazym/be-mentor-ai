from typing import Annotated

from fastapi import APIRouter, status as s, Query, Depends

from src.application.modules.interfaces import IModuleController
from src.application.directions.dtos import ProgressStatisticsDTO
from src.application.skills.dtos import UserSkillDTO
from src.application.users.dtos import UserDTO
from src.domain.base_dto import PaginationDTO
from src.domain.base_schema import PaginationSchema
from src.domain.responses import RESPONSE_401
from src.presentation.depends.controllers import get_module_controller
from src.presentation.depends.security import get_access_user

router = APIRouter(
    prefix="/modules",
    tags=["modules"],
)

@router.get(
    "/my",
    status_code=s.HTTP_200_OK,
    response_model=PaginationDTO[UserSkillDTO],
    response_model_exclude_none=True,
    responses={
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401,
    },
)
async def get_my_modules(
    controller: Annotated[IModuleController, Depends(get_module_controller)],
    user: UserDTO = Depends(get_access_user),
    populate_skill: bool = Query(False),
    pagination: PaginationSchema = Depends(PaginationSchema.as_query()),
):
    return await controller.get_my_modules(
        user_id=user.id,
        pagination=PaginationDTO[UserSkillDTO](**pagination.dict()),
        populate_skill=populate_skill,
    )

@router.get(
    "/{module_id}/statistics",
    status_code=s.HTTP_200_OK,
    response_model=ProgressStatisticsDTO,
    response_model_exclude_none=True,
    responses={
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401,
    },
)
async def get_module_statistics(
    controller: Annotated[IModuleController, Depends(get_module_controller)],
    module_id: int,
    user: UserDTO = Depends(get_access_user),
):
    return await controller.get_statistics(
        user_id=user.id,
        module_id=module_id,
    )
