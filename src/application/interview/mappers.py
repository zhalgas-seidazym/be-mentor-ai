from typing import Optional

from src.application.interview.dtos import InterviewSessionDTO, InterviewQuestionDTO
from src.application.interview.models import InterviewSession, InterviewQuestion


def interview_session_orm_to_dto(row: InterviewSession) -> Optional[InterviewSessionDTO]:
    return InterviewSessionDTO(
        id=row.id,
        user_id=row.user_id,
        status=row.status,
        current_main_index=row.current_main_index,
        total_main_questions=row.total_main_questions,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def interview_session_dto_to_orm(
    dto: InterviewSessionDTO,
    row: Optional[InterviewSession] = None,
) -> InterviewSession:
    row = row or InterviewSession()

    if dto.id is not None:
        row.id = dto.id

    if dto.user_id is not None:
        row.user_id = dto.user_id

    if dto.status is not None:
        row.status = dto.status

    if dto.current_main_index is not None:
        row.current_main_index = dto.current_main_index

    if dto.total_main_questions is not None:
        row.total_main_questions = dto.total_main_questions

    return row


def interview_question_orm_to_dto(row: InterviewQuestion) -> Optional[InterviewQuestionDTO]:
    return InterviewQuestionDTO(
        id=row.id,
        session_id=row.session_id,
        question_id=row.question_id,
        question_text=row.question_text,
        is_followup=row.is_followup,
        main_question_id=row.main_question_id,
        followup_index=row.followup_index,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def interview_question_dto_to_orm(
    dto: InterviewQuestionDTO,
    row: Optional[InterviewQuestion] = None,
) -> InterviewQuestion:
    row = row or InterviewQuestion()

    if dto.id is not None:
        row.id = dto.id

    if dto.session_id is not None:
        row.session_id = dto.session_id

    if dto.question_id is not None:
        row.question_id = dto.question_id

    if dto.question_text is not None:
        row.question_text = dto.question_text

    if dto.is_followup is not None:
        row.is_followup = dto.is_followup

    if dto.main_question_id is not None:
        row.main_question_id = dto.main_question_id

    if dto.followup_index is not None:
        row.followup_index = dto.followup_index

    return row
