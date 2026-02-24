from dataclasses import dataclass
from typing import Optional


@dataclass
class CountryDTO:
    id: Optional[int] = None
    name: Optional[str] = None

@dataclass
class CityDTO:
    id: Optional[int] = None
    name: Optional[str] = None
    country_id: Optional[int] = None
    country: Optional[CountryDTO] = None
