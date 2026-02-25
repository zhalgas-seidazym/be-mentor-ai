from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.application.locations.dtos import CityDTO


@dataclass
class UserDTO:
    id: Optional[int] = None
    email: Optional[str] = None
    password: Optional[str] = None
    name: Optional[str] = None
    city_id: Optional[int] = None
    city: Optional[CityDTO] = None
    is_onboarding_completed: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
