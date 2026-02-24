from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class UserDTO:
    id: Optional[int] = None
    email: Optional[str] = None
    password: Optional[str] = None
    name: Optional[str] = None
    is_onboarding_completed: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
