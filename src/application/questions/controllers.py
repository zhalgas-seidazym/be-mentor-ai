from typing import Optional

from src.application.questions.dtos import QuestionDTO
from src.application.questions.interfaces import IQuestionController, IQuestionRepository
from src.domain.base_dto import PaginationDTO


class QuestionController(IQuestionController):
    def __init__(
        self,
        question_repository: IQuestionRepository,
    ):
        self._question_repository = question_repository

    async def get_by_skill_id(
        self,
        skill_id: int,
        pagination: Optional[PaginationDTO[QuestionDTO]] = None,
        populate_skill: bool = False,
    ) -> PaginationDTO[QuestionDTO]:
        return await self._question_repository.get(
            pagination=pagination,
            skill_id=skill_id,
            populate_skill=populate_skill,
        )
