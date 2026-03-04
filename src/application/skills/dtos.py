from dataclasses import dataclass
from typing import Optional


@dataclass
class SkillDTO:
    id: Optional[int] = None
    name: Optional[str] = None


@dataclass
class UserSkillDTO:
    user_id: Optional[int] = None
    skill_id: Optional[int] = None
    skill: Optional[SkillDTO] = None
    to_learn: Optional[bool] = None
    match_percentage: Optional[float] = None
