from typing import Annotated, Dict, List, Union

from fastapi import APIRouter, Depends, Query, status as s
from fastapi.responses import JSONResponse

from src.application.vacancies.dtos import UserVacancyDTO, VacancyDTO, VacancySkillDTO
from src.application.vacancies.interfaces import IVacancyController
from src.application.users.dtos import UserDTO
from src.domain.responses import RESPONSE_401, RESPONSE_404
from src.presentation.depends.controllers import get_vacancy_controller
from src.presentation.depends.security import get_access_user


router = APIRouter(
    prefix="/vacancies",
    tags=["vacancies"],
)


@router.get(
    "/my",
    summary="Get my vacancies",
    status_code=s.HTTP_200_OK,
    response_model=Union[List[UserVacancyDTO], Dict[str, Union[str, int]]],
    response_model_exclude_none=True,
    responses={
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401,
        s.HTTP_202_ACCEPTED: {
            "description": "Vacancy search in progress",
            "content": {
                "application/json": {
                    "example": {"detail": "Поиск вакансий уже идет", "retry_after": 600}
                }
            }
        },
    },
)
async def get_my_vacancies(
    controller: Annotated[IVacancyController, Depends(get_vacancy_controller)],
    user: UserDTO = Depends(get_access_user),
    populate_vacancy: bool = Query(False),
):
    result = await controller.get_my_vacancies(
        user_id=user.id,
        populate_vacancy=populate_vacancy,
    )
    if isinstance(result, dict):
        retry_after = result.get("retry_after")
        headers = {"Retry-After": str(retry_after)} if retry_after is not None else None
        return JSONResponse(status_code=s.HTTP_202_ACCEPTED, content=result, headers=headers)
    return result

@router.get(
    "/{vacancy_id}",
    summary="Get vacancy by id",
    status_code=s.HTTP_200_OK,
    response_model=VacancyDTO,
    response_model_exclude_none=True,
    responses={
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401,
        s.HTTP_404_NOT_FOUND: RESPONSE_404,
    },
)
async def get_vacancy_by_id(
    controller: Annotated[IVacancyController, Depends(get_vacancy_controller)],
    vacancy_id: int,
    populate_skills: bool = Query(False),
    populate_city: bool = Query(False),
    populate_direction: bool = Query(False),
    user: UserDTO = Depends(get_access_user),
):
    return await controller.get_by_id(
        vacancy_id=vacancy_id,
        populate_skills=populate_skills,
        populate_city=populate_city,
        populate_direction=populate_direction,
    )

@router.get(
    "/{vacancy_id}/skills",
    summary="Get vacancy skills",
    status_code=s.HTTP_200_OK,
    response_model=List[VacancySkillDTO],
    response_model_exclude_none=True,
    responses={
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401,
        s.HTTP_404_NOT_FOUND: RESPONSE_404,
    },
)
async def get_vacancy_skills(
    controller: Annotated[IVacancyController, Depends(get_vacancy_controller)],
    vacancy_id: int,
    populate_skill: bool = Query(False),
    user: UserDTO = Depends(get_access_user),
):
    return await controller.get_vacancy_skills(
        vacancy_id=vacancy_id,
        populate_skill=populate_skill,
    )
