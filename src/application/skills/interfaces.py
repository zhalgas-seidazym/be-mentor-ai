from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

from src.application.skills.dtos import SkillDTO
from src.domain.base_dto import PaginationDTO


class ISkillRepository(ABC):
    @abstractmethod
    async def get_by_id(self, skill_id: int) -> Optional[SkillDTO]: ...

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[SkillDTO]: ...

    async def get(
            self,
            name: Optional[str] = None,
            pagination: Optional[Dict[str, Any]] = None,
    ) -> PaginationDTO[SkillDTO]: ...

    @abstractmethod
    async def add(self, name: str) -> Optional[SkillDTO]: ...

    @abstractmethod
    async def update(
        self,
        skill_id: int,
        name: str,
    ) -> Optional[SkillDTO]: ...

    @abstractmethod
    async def delete(self, skill_id: int) -> bool: ...

class ISkillController(ABC):
    @abstractmethod
    async def skill_autocomplete(self, pagination: PaginationDTO[SkillDTO], q: Optional[str] = None) -> PaginationDTO[SkillDTO]:  ...

    @abstractmethod
    async def get_by_id(self, skill_id: int) -> Optional[SkillDTO]: ...

    @abstractmethod
    async def create(self, name: str) -> Dict: ...

class ISkillSearchService(ABC):

    @abstractmethod
    async def create_index_if_not_exists(self) -> None: ...

    @abstractmethod
    async def delete_index(self) -> bool: ...

    @abstractmethod
    async def count(self) -> int: ...

    @abstractmethod
    async def bulk_index(self, skills: List[SkillDTO]) -> None: ...

    @abstractmethod
    async def index(self, skill_id: int, name: str) -> None: ...

    @abstractmethod
    async def delete(self, skill_id: int) -> None: ...

    @abstractmethod
    async def search(
        self,
        name: Optional[str] = None,
        pagination: Optional[PaginationDTO[SkillDTO]] = None,
    ) -> PaginationDTO[SkillDTO]: ...