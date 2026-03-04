from typing import Optional

from sqlalchemy import inspect
from sqlalchemy.orm import NO_VALUE

from src.application.questions.dtos import QuestionDTO, UserQuestionDTO
from src.application.questions.models import Question, UserQuestion
from src.application.skills.mappers import skill_orm_to_dto


def question_orm_to_dto(
    row: Question,
    populate_skill: bool = False,
) -> Optional[QuestionDTO]:
    skill_dto = None

    if populate_skill:
        state = inspect(row)
        skill_loaded = state.attrs.skill.loaded_value

        if skill_loaded is not None and skill_loaded is not NO_VALUE:
            skill_dto = skill_orm_to_dto(skill_loaded)

    return QuestionDTO(
        id=row.id,
        question=row.question,
        ideal_answer=row.ideal_answer,
        skill_id=row.skill_id,
        skill=skill_dto,
    )


def question_dto_to_orm(
    dto: QuestionDTO,
    row: Optional[Question] = None,
) -> Question:
    row = row or Question()

    if dto.id is not None:
        row.id = dto.id

    if dto.question is not None:
        row.question = dto.question

    if dto.ideal_answer is not None:
        row.ideal_answer = dto.ideal_answer

    if dto.skill_id is not None:
        row.skill_id = dto.skill_id

    return row


def user_question_orm_to_dto(
    row: UserQuestion,
    populate_question: bool = False,
) -> Optional[UserQuestionDTO]:
    question_dto = None

    if populate_question:
        state = inspect(row)
        question_loaded = state.attrs.question.loaded_value

        if question_loaded is not None and question_loaded is not NO_VALUE:
            question_dto = question_orm_to_dto(question_loaded, populate_skill=True)

    return UserQuestionDTO(
        id=row.id,
        user_id=row.user_id,
        question_id=row.question_id,
        user_answer=row.user_answer,
        feedback=row.feedback,
        status=row.status,
        question=question_dto,
    )


def user_question_dto_to_orm(
    dto: UserQuestionDTO,
    row: Optional[UserQuestion] = None,
) -> UserQuestion:
    row = row or UserQuestion()

    if dto.id is not None:
        row.id = dto.id

    if dto.user_id is not None:
        row.user_id = dto.user_id

    if dto.question_id is not None:
        row.question_id = dto.question_id

    if dto.user_answer is not None:
        row.user_answer = dto.user_answer

    if dto.feedback is not None:
        row.feedback = dto.feedback

    if dto.status is not None:
        row.status = dto.status

    return row
