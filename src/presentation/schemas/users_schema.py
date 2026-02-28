import re
from pydantic import BaseModel, EmailStr, field_validator
from fastapi import HTTPException, status

from src.domain.base_schema import PasswordSchema


class UserRegisterSchema(PasswordSchema):
    email: EmailStr
    code: str

class UserProfileCreateSchema(BaseModel):
    name: str
    city_id: int
    direction_id: int
    skill_ids: list[int]
