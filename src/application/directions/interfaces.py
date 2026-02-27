from abc import ABC, abstractmethod
from typing import Optional, List

from src.application.directions.dtos import DirectionDTO, SalaryDTO
from src.domain.base_dto import PaginationDTO


class IDirectionRepository(ABC):

    @abstractmethod
    async def get_by_id(
        self,
        direction_id: int,
    ) -> Optional[DirectionDTO]: ...

    @abstractmethod
    async def get_by_name(
        self,
        name: str,
    ) -> Optional[DirectionDTO]: ...

    @abstractmethod
    async def get(
        self,
        name: Optional[str] = None,
        pagination: Optional[PaginationDTO[DirectionDTO]] = None,
    ) -> PaginationDTO[DirectionDTO]: ...

    @abstractmethod
    async def add(
        self,
        dto: DirectionDTO,
    ) -> Optional[DirectionDTO]: ...

    @abstractmethod
    async def update(
        self,
        direction_id: int,
        dto: DirectionDTO,
    ) -> Optional[DirectionDTO]: ...

    @abstractmethod
    async def delete(
        self,
        direction_id: int,
    ) -> bool: ...

class ISalaryRepository(ABC):

    @abstractmethod
    async def get(
            self,
            city_id: Optional[int] = None,
            direction_id: Optional[int] = None,
            pagination: Optional[PaginationDTO[SalaryDTO]] = None,
            populate_city: bool = False,
            populate_direction: bool = False,
    ) -> PaginationDTO[SalaryDTO]: ...

    @abstractmethod
    async def get_by_city_and_direction(
        self,
        city_id: int,
        direction_id: int,
        populate_city: bool = False,
        populate_direction: bool = False,
    ) -> Optional[SalaryDTO]: ...

    @abstractmethod
    async def add(
        self,
        dto: SalaryDTO,
    ) -> Optional[SalaryDTO]: ...

    @abstractmethod
    async def update(
        self,
        salary_id: int,
        dto: SalaryDTO,
    ) -> Optional[SalaryDTO]: ...

    @abstractmethod
    async def delete(
        self,
        salary_id: int,
    ) -> bool: ...

class IDirectionSalaryController(ABC):

    @abstractmethod
    async def get_ai_directions(
            self,
            skills: List[str],
            city_id: int,
    ) -> List[SalaryDTO]: ...

    @abstractmethod
    async def direction_autocomplete(
            self,
            pagination: PaginationDTO[DirectionDTO],
            q: Optional[str] = None,
    ) -> PaginationDTO[DirectionDTO]: ...

class IDirectionSearchService(ABC):

    @abstractmethod
    async def create_index_if_not_exists(self) -> None: ...

    @abstractmethod
    async def delete_index(self) -> bool: ...

    @abstractmethod
    async def count(self) -> int: ...

    @abstractmethod
    async def bulk_index(self, directions: List[DirectionDTO]) -> None: ...

    @abstractmethod
    async def index(self, direction_id: int, name: str) -> None: ...

    @abstractmethod
    async def delete(self, direction_id: int) -> None: ...

    @abstractmethod
    async def search(
        self,
        name: Optional[str] = None,
        pagination: Optional[PaginationDTO[DirectionDTO]] = None,
    ) -> PaginationDTO[DirectionDTO]: ...

