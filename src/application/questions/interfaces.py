from abc import ABC, abstractmethod
from typing import Optional

from src.application.questions.dtos import QuestionDTO, UserQuestionDTO
from src.domain.base_dto import PaginationDTO


class IQuestionRepository(ABC):
    @abstractmethod
    async def add(self, dto: QuestionDTO) -> Optional[QuestionDTO]: ...

    @abstractmethod
    async def get(
        self,
        pagination: Optional[PaginationDTO[QuestionDTO]] = None,
        module_id: Optional[int] = None,
        q: Optional[str] = None,
        populate_skill: bool = False,
    ) -> PaginationDTO[QuestionDTO]: ...

    @abstractmethod
    async def get_by_id(
        self,
        question_id: int,
        populate_skill: bool = False,
    ) -> Optional[QuestionDTO]: ...

    @abstractmethod
    async def update(
        self,
        question_id: int,
        dto: QuestionDTO,
    ) -> Optional[QuestionDTO]: ...

    @abstractmethod
    async def delete(self, question_id: int) -> bool: ...


class IUserQuestionRepository(ABC):
    @abstractmethod
    async def add(self, dto: UserQuestionDTO) -> Optional[UserQuestionDTO]: ...

    @abstractmethod
    async def get(
        self,
        pagination: Optional[PaginationDTO[UserQuestionDTO]] = None,
        user_id: Optional[int] = None,
        module_id: Optional[int] = None,
        question_id: Optional[int] = None,
        populate_question: bool = False,
    ) -> PaginationDTO[UserQuestionDTO]: ...

    @abstractmethod
    async def get_by_id(
        self,
        user_question_id: int,
        populate_question: bool = False,
    ) -> Optional[UserQuestionDTO]: ...

    @abstractmethod
    async def update(
        self,
        user_question_id: int,
        dto: UserQuestionDTO,
    ) -> Optional[UserQuestionDTO]: ...

    @abstractmethod
    async def delete(self, user_question_id: int) -> bool: ...


class IQuestionController(ABC):
    @abstractmethod
    async def get_by_id(
        self,
        question_id: int,
        populate_skill: bool = False,
    ) -> Optional[QuestionDTO]: ...

    @abstractmethod
    async def get_by_module_id(
        self,
        module_id: int,
        pagination: Optional[PaginationDTO[QuestionDTO]] = None,
        populate_skill: bool = False,
    ) -> PaginationDTO[QuestionDTO]: ...

    @abstractmethod
    async def get_user_answers(
        self,
        user_id: int,
        pagination: Optional[PaginationDTO[UserQuestionDTO]] = None,
        module_id: Optional[int] = None,
        question_id: Optional[int] = None,
        populate_question: bool = False,
    ) -> PaginationDTO[UserQuestionDTO]: ...
