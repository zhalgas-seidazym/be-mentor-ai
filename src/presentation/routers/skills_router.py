from typing import Optional, Annotated, List

from fastapi import APIRouter, status as s, Query, Depends, Body

from src.application.skills.dtos import SkillDTO
from src.application.users.dtos import UserDTO, UserSkillDTO
from src.application.skills.interfaces import ISkillController
from src.application.users.dtos import UserDTO
from src.domain.base_dto import PaginationDTO
from src.domain.base_schema import PaginationSchema
from src.domain.responses import RESPONSE_404, RESPONSE_401, RESPONSE_409
from src.presentation.depends.controllers import get_skill_controller
from src.presentation.depends.security import get_access_user

router = APIRouter(
    prefix="/skills",
    tags=["skill"]
)

@router.post(
    '',
    status_code=s.HTTP_201_CREATED,
    response_model=SkillDTO,
    responses={
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401,
        s.HTTP_409_CONFLICT: RESPONSE_409
    }
)
async def create_skill(
        controller: Annotated[ISkillController, Depends(get_skill_controller)],
        name: str = Body(),
        user: UserDTO = Depends(get_access_user)
):
    return await controller.create(name)

@router.get(
    '/autocomplete',
    status_code=s.HTTP_200_OK,
    response_model=PaginationDTO[SkillDTO],
    responses={
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401,
    }
)
async def skill_autocomplete(
        controller: Annotated[ISkillController, Depends(get_skill_controller)],
        q: Optional[str] = Query(None),
        pagination: PaginationSchema = Depends(PaginationSchema.as_query())
):
    return await controller.skill_autocomplete(PaginationDTO[SkillDTO](**pagination.dict()), q=q)

@router.get(
    '/my',
    status_code=s.HTTP_200_OK,
    response_model=List[UserSkillDTO],
    response_model_exclude_none=True,
    responses={
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401,
    }
)
async def get_my_skills(
        controller: Annotated[ISkillController, Depends(get_skill_controller)],
        user: UserDTO = Depends(get_access_user),
        populate_skill: bool = Query(False),
):
    return await controller.get_my_skills(
        user_id=user.id,
        populate_skill=populate_skill,
    )

@router.get(
    '/{skill_id}',
    status_code=s.HTTP_200_OK,
    response_model=SkillDTO,
    responses={
        s.HTTP_404_NOT_FOUND: RESPONSE_404,
    }
)
async def get_skill_by_id(
        controller: Annotated[ISkillController, Depends(get_skill_controller)],
        skill_id: int,
):
    return await controller.get_by_id(skill_id)