from dataclasses import dataclass
from typing import Optional


@dataclass
class ModuleStatisticsDTO:
    total_questions: Optional[int] = None
    met_questions: Optional[int] = None
    correct_answers: Optional[int] = None
    incorrect_answers: Optional[int] = None
    readiness_percentage: Optional[float] = None
