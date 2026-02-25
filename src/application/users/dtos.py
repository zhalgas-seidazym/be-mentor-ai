from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

from src.application.locations.dtos import CityDTO
from src.application.skills.dtos import SkillDTO


@dataclass
class UserSkillDTO:
    user_id: Optional[int] = None
    skill_id: Optional[int] = None
    skill: Optional[SkillDTO] = None
    to_learn: Optional[bool] = None

@dataclass
class UserDTO:
    id: Optional[int] = None
    email: Optional[str] = None
    password: Optional[str] = None
    name: Optional[str] = None
    city_id: Optional[int] = None
    skills: Optional[List[UserSkillDTO]] = None
    city: Optional[CityDTO] = None
    is_onboarding_completed: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
