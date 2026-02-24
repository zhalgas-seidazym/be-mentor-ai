from dataclasses import dataclass
from typing import Optional


@dataclass
class SkillDTO:
    id: Optional[int] = None
    name: Optional[str] = None