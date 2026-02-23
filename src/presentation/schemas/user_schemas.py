import re
from pydantic import BaseModel, EmailStr, field_validator
from fastapi import HTTPException, status

from src.domain.base_schema import PasswordSchema


class UserRegisterSchema(PasswordSchema):
    email: EmailStr
    code: str