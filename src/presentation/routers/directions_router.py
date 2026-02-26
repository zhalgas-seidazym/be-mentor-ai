from typing import List, Annotated

from fastapi import APIRouter, status as s, Depends, Body

from src.application.directions.dtos import SalaryDTO
from src.application.directions.interfaces import IDirectionSalaryController
from src.domain.responses import *
from src.presentation.depends.controllers import get_direction_salary_controller

router = APIRouter(
    prefix="/directions",
    tags=["directions"]
)

@router.post(
    '/ai-directions',
    status_code=s.HTTP_200_OK,
    response_model=List[SalaryDTO],
    response_model_exclude_none=True,
    description="Get Ai recommended directions",
    responses={
        s.HTTP_400_BAD_REQUEST: RESPONSE_400,
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401,
    }
)
async def get_ai_directions(
        controller: Annotated[IDirectionSalaryController, Depends(get_direction_salary_controller)],
        city_id: int = Body(),
        skills: List[str] = Body(None)
):
    return await controller.get_ai_directions(skills, city_id)

