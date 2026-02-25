from typing import Optional, Annotated

from fastapi import APIRouter, status as s, Query, Depends

from src.application.skills.dtos import SkillDTO
from src.application.skills.interfaces import ISkillController
from src.domain.base_dto import PaginationDTO
from src.domain.base_schema import PaginationSchema
from src.domain.responses import RESPONSE_404, RESPONSE_401
from src.presentation.depends.controllers import get_skill_controller

router = APIRouter(
    prefix="/skill",
    tags=["skill"]
)

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