from abc import ABC, abstractmethod
from typing import Optional, Dict

from src.application.locations.dtos import CountryDTO, CityDTO
from src.domain.base_dto import PaginationDTO


class ICountryRepository(ABC):

    @abstractmethod
    async def get_by_id(
        self,
        country_id: int,
    ) -> Optional[CountryDTO]:
        ...

    @abstractmethod
    async def get_by_name(
        self,
        name: str,
    ) -> Optional[CountryDTO]:
        ...

    @abstractmethod
    async def get(
        self,
        name: Optional[str] = None,
        pagination: Optional[PaginationDTO[CountryDTO]] = None,
    ) -> PaginationDTO[CountryDTO]:
        ...


class ICityRepository(ABC):

    @abstractmethod
    async def get_by_id(
        self,
        city_id: int,
        populate_country: bool = False,
    ) -> Optional[CityDTO]:
        ...

    @abstractmethod
    async def get_by_name(
        self,
        name: str,
        populate_country: bool = False,
    ) -> Optional[CityDTO]:
        ...

    @abstractmethod
    async def get(
        self,
        name: Optional[str] = None,
        country_id: Optional[int] = None,
        pagination: Optional[PaginationDTO[CityDTO]] = None,
        populate_country: bool = False,
    ) -> PaginationDTO[CityDTO]:
        ...

class ILocationController(ABC):
    @abstractmethod
    async def get_countries_by_name(self, pagination: PaginationDTO[CountryDTO], q: Optional[str]) -> PaginationDTO[CountryDTO]: ...

    @abstractmethod
    async def get_country_by_id(self, country_id: int) -> Optional[CountryDTO]: ...

    @abstractmethod
    async def get_city_by_name_and_country_id(
            self,
            pagination: PaginationDTO[CityDTO],
            q: Optional[str],
            country_id: Optional[int],
            populate_country: bool = False,
    ) -> PaginationDTO[CityDTO]: ...