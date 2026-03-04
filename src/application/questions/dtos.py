from dataclasses import dataclass
from typing import Optional

from src.domain.value_objects import QuestionStatus
from src.application.skills.dtos import SkillDTO


@dataclass
class QuestionDTO:
    id: Optional[int] = None
    question: Optional[str] = None
    ideal_answer: Optional[str] = None
    skill_id: Optional[int] = None
    skill: Optional[SkillDTO] = None


@dataclass
class UserQuestionDTO:
    id: Optional[int] = None
    user_id: Optional[int] = None
    question_id: Optional[int] = None
    user_answer: Optional[str] = None
    feedback: Optional[str] = None
    status: Optional[QuestionStatus] = None
    question: Optional[QuestionDTO] = None
