from typing import Protocol, Optional, List

from src.application.directions.dtos import SalaryDTO
from src.application.users.dtos import UserSkillDTO
from src.domain.value_objects import ChatGPTModel


class IUoW(Protocol):
    ...

class IElasticSearchClient(Protocol):
    ...

class IJWTService(Protocol):
    def encode_token(
        self,
        data: dict,
        expires_delta: Optional[int] = None,
        is_access_token: bool = True
    ) -> str: ...

    def decode_token(self, token: str) -> dict: ...


class IEmailService(Protocol):
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html: bool = False
    ) -> None: ...

class IOpenAIService(Protocol):

    async def get_specializations(
        self,
        skills: List[str],
        country: str,
        city: str,
        model: ChatGPTModel,
        temperature: float = 0.4,
    ) -> List[SalaryDTO]:
        ...

    async def get_direction_description(
        self,
        direction_name: str,
        model: ChatGPTModel,
        temperature: float = 0.2,
    ) -> str:
        ...

    async def get_direction_theoretical_skills(
        self,
        direction_name: str,
        skills: List[str],
        model: ChatGPTModel,
        temperature: float = 0.3,
    ) -> List[UserSkillDTO]:
        ...
