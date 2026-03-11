from typing import Optional

from fastapi import HTTPException, status as s

from src.application.questions.dtos import QuestionDTO, UserQuestionDTO
from src.application.questions.interfaces import (
    IQuestionController,
    IQuestionRepository,
    IUserQuestionRepository,
)
from src.domain.base_dto import PaginationDTO


class QuestionController(IQuestionController):
    def __init__(
        self,
        question_repository: IQuestionRepository,
        user_question_repository: IUserQuestionRepository,
    ):
        self._question_repository = question_repository
        self._user_question_repository = user_question_repository

    async def get_by_id(
        self,
        question_id: int,
        populate_skill: bool = False,
    ) -> Optional[QuestionDTO]:
        res = await self._question_repository.get_by_id(
            question_id=question_id,
            populate_skill=populate_skill,
        )
        if res is None:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=f"Question {question_id} not found")
        return res

    async def get_by_module_id(
        self,
        module_id: int,
        pagination: Optional[PaginationDTO[QuestionDTO]] = None,
        populate_skill: bool = False,
    ) -> PaginationDTO[QuestionDTO]:
        return await self._question_repository.get(
            pagination=pagination,
            module_id=module_id,
            populate_skill=populate_skill,
        )

    async def get_user_answers(
        self,
        user_id: int,
        pagination: Optional[PaginationDTO[UserQuestionDTO]] = None,
        module_id: Optional[int] = None,
        question_id: Optional[int] = None,
        populate_question: bool = False,
    ) -> PaginationDTO[UserQuestionDTO]:
        if question_id is None and module_id is None:
            raise HTTPException(
                status_code=s.HTTP_400_BAD_REQUEST,
                detail="skill_id is required when question_id is not provided",
            )

        return await self._user_question_repository.get(
            pagination=pagination,
            user_id=user_id,
            module_id=module_id if question_id is None else None,
            question_id=question_id,
            populate_question=populate_question,
        )
