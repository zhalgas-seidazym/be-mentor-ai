from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator

from src.domain.base_schema import PasswordSchema, NewPasswordSchema


class UserRegisterSchema(PasswordSchema):
    email: EmailStr
    code: str

class UserProfileCreateSchema(BaseModel):
    name: str
    city_id: int
    direction_id: int
    skill_ids: list[int]

class UserProfileUpdateSchema(NewPasswordSchema, PasswordSchema):
    name: Optional[str] = None
    city_id: Optional[int] = None
    password: Optional[str] = None
    new_password: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password_optional(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return super().validate_password(value)

    @field_validator("new_password")
    @classmethod
    def validate_new_password_optional(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return super().validate_new_password(value)
