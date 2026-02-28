from typing import List, Annotated, Optional

from fastapi import APIRouter, status as s, Depends, Body, Query

from src.application.directions.dtos import SalaryDTO, DirectionDTO
from src.application.directions.interfaces import IDirectionSalaryController
from src.application.users.dtos import UserDTO
from src.domain.base_dto import PaginationDTO
from src.domain.base_schema import PaginationSchema
from src.domain.responses import *
from src.presentation.depends.controllers import get_direction_salary_controller
from src.presentation.depends.security import get_access_user

router = APIRouter(
    prefix="/directions",
    tags=["directions"]
)

@router.post(
    '',
    status_code=s.HTTP_201_CREATED,
    response_model=DirectionDTO,
    response_model_exclude_none=True,
    responses={
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401,
        s.HTTP_408_REQUEST_TIMEOUT: RESPONSE_408,
        s.HTTP_409_CONFLICT: RESPONSE_409,
    }
)
async def create_direction(
        controller: Annotated[IDirectionSalaryController, Depends(get_direction_salary_controller)],
        name: str = Body(),
        user: UserDTO = Depends(get_access_user)
):
    return await controller.create_direction(name)

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

@router.get(
    '/autocomplete',
    status_code=s.HTTP_200_OK,
    response_model=PaginationDTO[DirectionDTO],
    responses={
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401,
    }
)
async def direction_autocomplete(
        controller: Annotated[IDirectionSalaryController, Depends(get_direction_salary_controller)],
        q: Optional[str] = Query(None),
        pagination: PaginationSchema = Depends(PaginationSchema.as_query())
):
    return await controller.direction_autocomplete(PaginationDTO[DirectionDTO](**pagination.dict()), q=q)
