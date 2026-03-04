from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.domain.value_objects import InterviewStatus
from src.application.questions.dtos import QuestionDTO


@dataclass
class InterviewSessionDTO:
    id: Optional[int] = None
    user_id: Optional[int] = None
    status: Optional[InterviewStatus] = None
    current_main_index: Optional[int] = None
    total_main_questions: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class InterviewQuestionDTO:
    id: Optional[int] = None
    session_id: Optional[int] = None
    question_id: Optional[int] = None
    question_text: Optional[str] = None
    question: Optional[QuestionDTO] = None
    is_followup: Optional[bool] = None
    main_question_id: Optional[int] = None
    followup_index: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
