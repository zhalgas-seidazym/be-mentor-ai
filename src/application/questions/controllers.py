from typing import Optional

from fastapi import HTTPException, status as s

from src.application.questions.dtos import QuestionDTO, UserQuestionDTO
from src.application.questions.interfaces import (
    IQuestionController,
    IQuestionRepository,
    IUserQuestionRepository,
)
from src.application.skills.interfaces import ISkillRepository, IUserSkillRepository
from src.domain.base_dto import PaginationDTO


class QuestionController(IQuestionController):
    def __init__(
        self,
        question_repository: IQuestionRepository,
        user_question_repository: IUserQuestionRepository,
        skill_repository: ISkillRepository,
        user_skill_repository: IUserSkillRepository,
    ):
        self._question_repository = question_repository
        self._user_question_repository = user_question_repository
        self._skill_repository = skill_repository
        self._user_skill_repository = user_skill_repository

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
        user_id: int,
        module_id: int,
        pagination: Optional[PaginationDTO[QuestionDTO]] = None,
        populate_skill: bool = False,
    ) -> PaginationDTO[QuestionDTO]:
        module = await self._skill_repository.get_by_id(module_id)
        if module is None:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=f"Module {module_id} not found")
        user_module = await self._user_skill_repository.get_by_user_and_skill(
            user_id=user_id,
            skill_id=module_id,
        )
        if user_module is None or not user_module.to_learn:
            raise HTTPException(status_code=s.HTTP_403_FORBIDDEN, detail=f"You do not have access to this module")
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
        if module_id is not None:
            module = await self._skill_repository.get_by_id(module_id)
            if module is None:
                raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=f"Module {module_id} not found")

            user_module = await self._user_skill_repository.get_by_user_and_skill(
                user_id=user_id,
                skill_id=module_id,
            )
            if user_module is None or not user_module.to_learn:
                raise HTTPException(status_code=s.HTTP_403_FORBIDDEN, detail=f"User do not have access to this module")

        if question_id is not None:
            question = await self._question_repository.get_by_id(question_id=question_id)
            if question is None:
                raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=f"Question {question_id} not found")

        return await self._user_question_repository.get(
            pagination=pagination,
            user_id=user_id,
            module_id=module_id,
            question_id=question_id,
            populate_question=populate_question,
        )
