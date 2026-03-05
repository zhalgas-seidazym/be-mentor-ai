from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class LearningRecommendationDTO:
    id: Optional[int] = None
    skill_id: Optional[int] = None
    source: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
