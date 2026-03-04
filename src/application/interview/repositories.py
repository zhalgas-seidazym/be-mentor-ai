from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.application.interview.dtos import InterviewSessionDTO, InterviewQuestionDTO
from src.application.interview.interfaces import IInterviewSessionRepository, IInterviewQuestionRepository
from src.application.interview.mappers import (
    interview_session_dto_to_orm,
    interview_session_orm_to_dto,
    interview_question_dto_to_orm,
    interview_question_orm_to_dto,
)
from src.application.interview.models import InterviewSession, InterviewQuestion
from src.domain.value_objects import InterviewStatus


class InterviewSessionRepository(IInterviewSessionRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, dto: InterviewSessionDTO) -> Optional[InterviewSessionDTO]:
        row = interview_session_dto_to_orm(dto)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return interview_session_orm_to_dto(row)

    async def get_by_id(self, session_id: int) -> Optional[InterviewSessionDTO]:
        query = select(InterviewSession).where(InterviewSession.id == session_id)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()
        return interview_session_orm_to_dto(row) if row else None

    async def update(self, session_id: int, dto: InterviewSessionDTO) -> Optional[InterviewSessionDTO]:
        query = select(InterviewSession).where(InterviewSession.id == session_id)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return None

        row = interview_session_dto_to_orm(dto, row)
        await self._session.flush()
        await self._session.refresh(row)
        return interview_session_orm_to_dto(row)

    async def get_active_by_user(self, user_id: int) -> Optional[InterviewSessionDTO]:
        query = select(InterviewSession).where(
            InterviewSession.user_id == user_id,
            InterviewSession.status == InterviewStatus.ACTIVE,
        ).limit(1)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()
        return interview_session_orm_to_dto(row) if row else None


class InterviewQuestionRepository(IInterviewQuestionRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add_many(self, dtos: List[InterviewQuestionDTO]) -> List[InterviewQuestionDTO]:
        rows = [interview_question_dto_to_orm(dto) for dto in dtos]
        self._session.add_all(rows)
        await self._session.flush()
        for row in rows:
            await self._session.refresh(row)
        return [interview_question_orm_to_dto(r) for r in rows]

    async def add(self, dto: InterviewQuestionDTO) -> Optional[InterviewQuestionDTO]:
        row = interview_question_dto_to_orm(dto)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return interview_question_orm_to_dto(row)

    async def get_by_id(self, interview_question_id: int, populate_question: bool = False) -> Optional[InterviewQuestionDTO]:
        query = select(InterviewQuestion)
        if populate_question:
            query = query.options(selectinload(InterviewQuestion.question))
        query = query.where(InterviewQuestion.id == interview_question_id)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()
        return interview_question_orm_to_dto(row, populate_question=populate_question) if row else None

    async def get_main_questions(self, session_id: int) -> List[InterviewQuestionDTO]:
        query = select(InterviewQuestion).where(
            InterviewQuestion.session_id == session_id,
            InterviewQuestion.is_followup.is_(False),
        )
        result = await self._session.execute(query)
        rows = result.scalars().all()
        return [interview_question_orm_to_dto(r) for r in rows]

    async def get_current_main(self, session_id: int, index: int) -> Optional[InterviewQuestionDTO]:
        query = select(InterviewQuestion).where(
            InterviewQuestion.session_id == session_id,
            InterviewQuestion.is_followup.is_(False),
        ).order_by(InterviewQuestion.id).offset(index - 1).limit(1)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()
        return interview_question_orm_to_dto(row) if row else None

    async def count_followups(self, session_id: int, main_question_id: int) -> int:
        query = select(func.count()).select_from(InterviewQuestion).where(
            InterviewQuestion.session_id == session_id,
            InterviewQuestion.main_question_id == main_question_id,
            InterviewQuestion.is_followup.is_(True),
        )
        result = await self._session.execute(query)
        return int(result.scalar_one())
