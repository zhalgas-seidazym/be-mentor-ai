import random
from typing import List

from fastapi import HTTPException, status as s

from src.application.interview.dtos import InterviewSessionDTO, InterviewQuestionDTO
from src.application.interview.interfaces import IInterviewController, IInterviewSessionRepository, IInterviewQuestionRepository
from src.application.questions.dtos import QuestionDTO
from src.application.questions.interfaces import IQuestionRepository
from src.application.skills.interfaces import IUserSkillRepository
from src.domain.base_dto import PaginationDTO
from src.domain.interfaces import IUoW


class InterviewController(IInterviewController):
    def __init__(
        self,
        interview_session_repository: IInterviewSessionRepository,
        interview_question_repository: IInterviewQuestionRepository,
        question_repository: IQuestionRepository,
        user_skill_repository: IUserSkillRepository,
        uow: IUoW,
    ):
        self._interview_session_repository = interview_session_repository
        self._interview_question_repository = interview_question_repository
        self._question_repository = question_repository
        self._user_skill_repository = user_skill_repository
        self._uow = uow

    async def start(self, user_id: int) -> dict:
        modules = await self._user_skill_repository.get_by_user_id(
            user_id=user_id,
            to_learn=True,
        )
        skills = [m.skill_id for m in (modules.items or []) if m.skill_id is not None]

        if not skills:
            raise HTTPException(status_code=s.HTTP_400_BAD_REQUEST, detail="No modules to learn")

        questions: List[QuestionDTO] = []
        for skill_id in skills:
            res = await self._question_repository.get(
                pagination=None,
                skill_id=skill_id,
            )
            if res.items:
                questions.extend(res.items)

        if len(questions) < 10:
            raise HTTPException(status_code=s.HTTP_400_BAD_REQUEST, detail="Not enough questions to start interview")

        random.shuffle(questions)
        selected = questions[:10]

        async with self._uow:
            session = await self._interview_session_repository.add(
                InterviewSessionDTO(
                    user_id=user_id,
                    current_main_index=1,
                    total_main_questions=10,
                )
            )

            question_rows = [
                InterviewQuestionDTO(
                    session_id=session.id,
                    question_id=q.id,
                    is_followup=False,
                )
                for q in selected
                if q.id is not None
            ]

            created_questions = await self._interview_question_repository.add_many(question_rows)

        first_question = created_questions[0]
        first_question_dto = next((q for q in selected if q.id == first_question.question_id), None)

        return {
            "session_id": session.id,
            "main_question_index": 1,
            "total_main_questions": 10,
            "question": {
                "interview_question_id": first_question.id,
                "question_id": first_question.question_id,
                "text": first_question_dto.question if first_question_dto else None,
            },
            "followup_limit": 2,
        }
