from typing import Annotated

from fastapi import APIRouter, status as s, Depends, Query

from src.application.questions.dtos import QuestionDTO
from src.application.questions.interfaces import IQuestionController
from src.application.users.dtos import UserDTO
from src.domain.base_dto import PaginationDTO
from src.domain.base_schema import PaginationSchema
from src.domain.responses import RESPONSE_401
from src.presentation.depends.controllers import get_question_controller
from src.presentation.depends.security import get_access_user

router = APIRouter(
    prefix="/questions",
    tags=["questions"],
)

@router.get(
    "/{skill_id}",
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
