from abc import ABC, abstractmethod
from typing import Optional, List

from src.application.interview.dtos import InterviewSessionDTO, InterviewQuestionDTO


class IInterviewSessionRepository(ABC):
    @abstractmethod
    async def add(self, dto: InterviewSessionDTO) -> Optional[InterviewSessionDTO]: ...

    @abstractmethod
    async def get_by_id(self, session_id: int) -> Optional[InterviewSessionDTO]: ...

    @abstractmethod
    async def update(self, session_id: int, dto: InterviewSessionDTO) -> Optional[InterviewSessionDTO]: ...


class IInterviewQuestionRepository(ABC):
    @abstractmethod
    async def add_many(self, dtos: List[InterviewQuestionDTO]) -> List[InterviewQuestionDTO]: ...

    @abstractmethod
    async def add(self, dto: InterviewQuestionDTO) -> Optional[InterviewQuestionDTO]: ...

    @abstractmethod
    async def get_by_id(self, interview_question_id: int, populate_question: bool = False) -> Optional[InterviewQuestionDTO]: ...

    @abstractmethod
    async def get_main_questions(self, session_id: int) -> List[InterviewQuestionDTO]: ...

    @abstractmethod
    async def get_current_main(self, session_id: int, index: int) -> Optional[InterviewQuestionDTO]: ...

    @abstractmethod
    async def count_followups(self, session_id: int, main_question_id: int) -> int: ...


class IInterviewController(ABC):
    @abstractmethod
    async def start(self, user_id: int) -> dict: ...
