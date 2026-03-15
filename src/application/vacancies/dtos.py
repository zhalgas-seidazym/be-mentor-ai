from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

from src.application.locations.dtos import CityDTO
from src.application.directions.dtos import DirectionDTO
from src.application.skills.dtos import SkillDTO
from src.domain.value_objects import VacancyType


@dataclass
class VacancyDTO:
    id: Optional[int] = None
    title: Optional[str] = None
    direction_id: Optional[int] = None
    city_id: Optional[int] = None
    salary_amount: Optional[float] = None
    salary_currency: Optional[str] = None
    vacancy_type: Optional[VacancyType] = None
    url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    vacancy_skills: Optional[List["VacancySkillDTO"]] = None
    city: Optional[CityDTO] = None
    direction: Optional[DirectionDTO] = None


@dataclass
class VacancySkillDTO:
    vacancy_id: Optional[int] = None
    skill_id: Optional[int] = None
    skill: Optional[SkillDTO] = None


@dataclass
class UserVacancyDTO:
    user_id: Optional[int] = None
    vacancy_id: Optional[int] = None
    vacancy: Optional[VacancyDTO] = None
