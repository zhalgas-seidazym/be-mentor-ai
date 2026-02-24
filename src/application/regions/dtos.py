from dataclasses import dataclass
from typing import Optional, List

from src.domain.base_dto import BaseDTOMixin, PaginationDTO


@dataclass
class CountryDTO(BaseDTOMixin):
    id: Optional[int] = None
    name: Optional[str] = None


@dataclass
class PaginationCountryDTO(PaginationDTO, BaseDTOMixin):
    items: Optional[List[CountryDTO]] = None

@dataclass
class CityDTO(BaseDTOMixin):
    id: Optional[int] = None
    name: Optional[str] = None
