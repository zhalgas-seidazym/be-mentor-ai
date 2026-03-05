from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, List

from src.application.directions.dtos import DirectionDTO
from src.application.locations.dtos import CityDTO
from src.application.skills.dtos import SkillDTO, UserSkillDTO


@dataclass
class UserDTO:
    id: Optional[int] = None
    email: Optional[str] = None
    password: Optional[str] = None
    name: Optional[str] = None
    city_id: Optional[int] = None
    direction_id: Optional[int] = None
    is_onboarding_completed: Optional[bool] = None
    current_streak: Optional[int] = None
    longest_streak: Optional[int] = None
    last_interview_day: Optional[date] = None
    timezone: Optional[str] = None
    skills: Optional[List[UserSkillDTO]] = None
    modules: Optional[List[UserSkillDTO]] = None
    direction: Optional[DirectionDTO] = None
    city: Optional[CityDTO] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
