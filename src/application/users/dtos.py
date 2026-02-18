from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from fastapi import UploadFile

from src.domain.base_dto import BaseDTOMixin


@dataclass
class UserDTO(BaseDTOMixin):
    id: Optional[int] = None
    email: Optional[str] = None
    password: Optional[str] = None
    name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
