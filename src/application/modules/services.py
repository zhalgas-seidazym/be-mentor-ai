from typing import Optional, Dict

from src.application.directions.dtos import ProgressStatisticsDTO
from src.application.modules.interfaces import IModuleStatisticsService
from src.application.questions.interfaces import IQuestionRepository, IUserQuestionRepository
from src.domain.value_objects import QuestionStatus


class ModuleStatisticsService(IModuleStatisticsService):
    def __init__(
        self,
        question_repository: IQuestionRepository,
        user_question_repository: IUserQuestionRepository,
    ):
        self._question_repository = question_repository
        self._user_question_repository = user_question_repository

    async def get_statistics(
        self,
        user_id: int,
        module_id: int,
    ) -> ProgressStatisticsDTO:

        questions_page = await self._question_repository.get(
            pagination=None,
            module_id=module_id,
        )
        total_questions = questions_page.total or 0

        user_questions_page = await self._user_question_repository.get(
            pagination=None,
            user_id=user_id,
            module_id=module_id,
        )
        user_questions = user_questions_page.items or []

        met_question_ids = {uq.question_id for uq in user_questions if uq.question_id is not None}
        met_questions = len(met_question_ids)

        latest_by_question: Dict[int, int] = {}
        status_by_question: Dict[int, QuestionStatus] = {}

        for uq in user_questions:
            if uq.question_id is None or uq.id is None or uq.status is None:
                continue

            prev_id = latest_by_question.get(uq.question_id)
            if prev_id is None or uq.id > prev_id:
                latest_by_question[uq.question_id] = uq.id
                status_by_question[uq.question_id] = uq.status

        correct_answers = sum(1 for s in status_by_question.values() if s == QuestionStatus.SATISFACTORY)
        incorrect_answers = sum(1 for s in status_by_question.values() if s == QuestionStatus.UNSATISFACTORY)

        readiness_percentage = 0.0
        if total_questions > 0:
            readiness_percentage = (correct_answers / total_questions) * 100

        return ProgressStatisticsDTO(
            total_questions=total_questions,
            met_questions=met_questions,
            correct_answers=correct_answers,
            incorrect_answers=incorrect_answers,
            readiness_percentage=readiness_percentage,
        )
