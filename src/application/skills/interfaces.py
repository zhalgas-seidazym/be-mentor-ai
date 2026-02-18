from abc import ABC, abstractmethod
from typing import Optional

from src.application.skills.dtos import SkillDTO


class ISkillRepository(ABC):

    @abstractmethod
    async def get_by_id(self, skill_id: int) -> Optional[SkillDTO]:
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[SkillDTO]:
        pass

    @abstractmethod
    async def add(self, name: str) -> Optional[SkillDTO]:
        pass

    @abstractmethod
    async def update(
        self,
        skill_id: int,
        name: str,
    ) -> Optional[SkillDTO]:
        pass

    @abstractmethod
    async def delete(self, skill_id: int) -> bool:
        pass