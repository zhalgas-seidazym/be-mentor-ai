from typing import Annotated, Optional

from fastapi import APIRouter, status as s, Depends, Query

from src.application.questions.dtos import QuestionDTO, UserQuestionDTO
from src.application.questions.interfaces import IQuestionController
from src.application.users.dtos import UserDTO
from src.domain.base_dto import PaginationDTO
from src.domain.base_schema import PaginationSchema
from src.domain.responses import RESPONSE_400, RESPONSE_401, RESPONSE_404
from src.presentation.depends.controllers import get_question_controller
from src.presentation.depends.security import get_access_user

router = APIRouter(
    prefix="/questions",
    tags=["questions"],
)

@router.get(
    "/module/{skill_id}",
    summary="Get questions by skill",
    status_code=s.HTTP_200_OK,
    response_model=PaginationDTO[QuestionDTO],
    response_model_exclude_none=True,
    responses={
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401,
    },
)
async def get_questions_by_skill_id(
    controller: Annotated[IQuestionController, Depends(get_question_controller)],
    skill_id: int,
    user: UserDTO = Depends(get_access_user),
    populate_skill: bool = Query(False),
    pagination: PaginationSchema = Depends(PaginationSchema.as_query()),
):
    return await controller.get_by_skill_id(
        skill_id=skill_id,
        pagination=PaginationDTO[QuestionDTO](**pagination.dict()),
        populate_skill=populate_skill,
    )

@router.get(
    "/user-answers",
    summary="Get my answers",
    status_code=s.HTTP_200_OK,
    response_model=PaginationDTO[UserQuestionDTO],
    response_model_exclude_none=True,
    responses={
        s.HTTP_400_BAD_REQUEST: RESPONSE_400,
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401,
    },
)
async def get_user_answers(
    controller: Annotated[IQuestionController, Depends(get_question_controller)],
    user: UserDTO = Depends(get_access_user),
    module_id: Optional[int] = Query(None),
    question_id: Optional[int] = Query(None),
    populate_question: bool = Query(False),
    pagination: PaginationSchema = Depends(PaginationSchema.as_query()),
):
    return await controller.get_user_answers(
        user_id=user.id,
        pagination=PaginationDTO[UserQuestionDTO](**pagination.dict()),
        module_id=module_id,
        question_id=question_id,
        populate_question=populate_question,
    )


@router.get(
    "/{question_id}",
    summary="Get question by id",
    status_code=s.HTTP_200_OK,
    response_model=QuestionDTO,
    response_model_exclude_none=True,
    responses={
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401,
        s.HTTP_404_NOT_FOUND: RESPONSE_404,
    },
)
async def get_question_by_id(
    controller: Annotated[IQuestionController, Depends(get_question_controller)],
    question_id: int,
    user: UserDTO = Depends(get_access_user),
    populate_skill: bool = Query(False),
):
    return await controller.get_by_id(
        question_id=question_id,
        populate_skill=populate_skill,
    )
