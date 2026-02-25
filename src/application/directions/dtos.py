from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.application.locations.dtos import CityDTO


@dataclass
class DirectionDTO:
    id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class SalaryDTO:
    id: Optional[int] = None
    direction_id: Optional[int] = None
    city_id: Optional[int] = None
    amount: Optional[float] = None
    currency: Optional[str] = None

    direction: Optional[DirectionDTO] = None
    city: Optional[CityDTO] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None