from typing import Optional, Annotated

from fastapi import APIRouter, status as s, Query, Depends

from src.application.skills.dtos import PaginationSkillDTO
from src.application.skills.interfaces import ISkillController
from src.domain.responses import RESPONSE_404, RESPONSE_401
from src.presentation.depends.controllers import get_skill_controller

router = APIRouter(
    prefix="/skill",
    tags=["skill"]
)

@router.get(
    '/skill/autocomplete',
    status_code=s.HTTP_200_OK,
    response_model=PaginationSkillDTO,
    responses={
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401,
    }
)
async def skill_autocomplete(
        controller: Annotated[ISkillController, Depends(get_skill_controller)],
        q: Optional[str] = Query(None),
        per_page: Optional[int] = Query(None),
        page: Optional[int] = Query(None)
):
    return await controller.skill_autocomplete(PaginationSkillDTO(per_page=per_page, page=page), q=q)