from typing import Optional, List

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.application.questions.dtos import QuestionDTO, UserQuestionDTO
from src.application.questions.interfaces import IQuestionRepository, IUserQuestionRepository
from src.application.questions.models import Question, UserQuestion
from src.application.questions.mappers import (
    question_orm_to_dto,
    question_dto_to_orm,
    user_question_orm_to_dto,
    user_question_dto_to_orm,
)
from src.domain.base_dto import PaginationDTO


class QuestionRepository(IQuestionRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    def _base_query(self, populate_skill: bool = False):
        query = select(Question)

        if populate_skill:
            query = query.options(
                selectinload(Question.skill)
            )

        return query

    async def add(self, dto: QuestionDTO) -> Optional[QuestionDTO]:
        row = question_dto_to_orm(dto)

        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)

        return question_orm_to_dto(row)

    async def get(
        self,
        pagination: Optional[PaginationDTO[QuestionDTO]] = None,
        module_id: Optional[int] = None,
        q: Optional[str] = None,
        populate_skill: bool = False,
    ) -> PaginationDTO[QuestionDTO]:

        base_query = self._base_query(populate_skill)

        if module_id is not None:
            base_query = base_query.where(Question.skill_id == module_id)

        if q:
            base_query = base_query.where(Question.question.ilike(f"%{q}%"))

        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await self._session.execute(count_query)
        total = count_result.scalar_one()

        if pagination is None or pagination.per_page is None:
            query = base_query
            page = 1
            per_page = total
        else:
            page = max(pagination.page or 1, 1)
            per_page = max(pagination.per_page or 10, 1)
            offset = (page - 1) * per_page
            query = base_query.offset(offset).limit(per_page)

        result = await self._session.execute(query)
        rows = result.scalars().all()

        items: List[QuestionDTO] = [
            question_orm_to_dto(row, populate_skill=populate_skill)
            for row in rows
        ]

        return PaginationDTO[QuestionDTO](
            page=page,
            per_page=per_page,
            total=total,
            items=items,
        )

    async def get_by_id(
        self,
        question_id: int,
        populate_skill: bool = False,
    ) -> Optional[QuestionDTO]:
        query = self._base_query(populate_skill).where(Question.id == question_id)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()
        return question_orm_to_dto(row, populate_skill=populate_skill) if row else None

    async def update(
        self,
        question_id: int,
        dto: QuestionDTO,
    ) -> Optional[QuestionDTO]:
        query = select(Question).where(Question.id == question_id)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return None

        row = question_dto_to_orm(dto, row)
        await self._session.flush()
        await self._session.refresh(row)

        return question_orm_to_dto(row)

    async def delete(self, question_id: int) -> bool:
        query = select(Question).where(Question.id == question_id)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return False

        await self._session.delete(row)
        return True


class UserQuestionRepository(IUserQuestionRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    def _base_query(self, populate_question: bool = False):
        query = select(UserQuestion)

        if populate_question:
            query = query.options(
                selectinload(UserQuestion.question)
                .selectinload(Question.skill)
            )

        return query

    async def add(self, dto: UserQuestionDTO) -> Optional[UserQuestionDTO]:
        row = user_question_dto_to_orm(dto)

        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)

        return user_question_orm_to_dto(row)

    async def get(
        self,
        pagination: Optional[PaginationDTO[UserQuestionDTO]] = None,
        user_id: Optional[int] = None,
        module_id: Optional[int] = None,
        question_id: Optional[int] = None,
        populate_question: bool = False,
    ) -> PaginationDTO[UserQuestionDTO]:

        base_query = self._base_query(populate_question)

        if user_id is not None:
            base_query = base_query.where(UserQuestion.user_id == user_id)

        if question_id is not None:
            base_query = base_query.where(UserQuestion.question_id == question_id)

        if module_id is not None:
            base_query = base_query.join(Question).where(Question.skill_id == module_id)

        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await self._session.execute(count_query)
        total = count_result.scalar_one()

        if pagination is None or pagination.per_page is None:
            query = base_query
            page = 1
            per_page = total
        else:
            page = max(pagination.page or 1, 1)
            per_page = max(pagination.per_page or 10, 1)
            offset = (page - 1) * per_page
            query = base_query.offset(offset).limit(per_page)

        result = await self._session.execute(query)
        rows = result.scalars().all()

        items: List[UserQuestionDTO] = [
            user_question_orm_to_dto(row, populate_question=populate_question)
            for row in rows
        ]

        return PaginationDTO[UserQuestionDTO](
            page=page,
            per_page=per_page,
            total=total,
            items=items,
        )

    async def get_by_id(
        self,
        user_question_id: int,
        populate_question: bool = False,
    ) -> Optional[UserQuestionDTO]:
        query = self._base_query(populate_question).where(UserQuestion.id == user_question_id)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()
        return user_question_orm_to_dto(row, populate_question=populate_question) if row else None

    async def update(
        self,
        user_question_id: int,
        dto: UserQuestionDTO,
    ) -> Optional[UserQuestionDTO]:
        query = select(UserQuestion).where(UserQuestion.id == user_question_id)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return None

        row = user_question_dto_to_orm(dto, row)
        await self._session.flush()
        await self._session.refresh(row)

        return user_question_orm_to_dto(row)

    async def delete(self, user_question_id: int) -> bool:
        query = select(UserQuestion).where(UserQuestion.id == user_question_id)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return False

        await self._session.delete(row)
        return True

    async def delete_by_user(
        self,
        user_id: int,
    ) -> int:
        result = await self._session.execute(
            delete(UserQuestion).where(UserQuestion.user_id == user_id)
        )
        return int(result.rowcount or 0)

    async def delete_by_user_and_module(
        self,
        user_id: int,
        module_id: int,
    ) -> int:
        question_ids_subq = select(Question.id).where(Question.skill_id == module_id)
        result = await self._session.execute(
            delete(UserQuestion).where(
                UserQuestion.user_id == user_id,
                UserQuestion.question_id.in_(question_ids_subq),
            )
        )
        return int(result.rowcount or 0)
