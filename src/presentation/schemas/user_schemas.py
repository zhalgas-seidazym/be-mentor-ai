import re
from pydantic import BaseModel, EmailStr, field_validator
from fastapi import HTTPException, status


class UserRegisterSchema(BaseModel):
    email: EmailStr
    password: str
    code: str

    # @field_validator("password")
    # @classmethod
    # def validate_password(cls, value: str) -> str:
    #     pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$"
    #
    #     if not re.match(pattern, value):
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail= "Password must be at least 8 characters long and contain one uppercase letter, one lowercase letter, and one digit"
    #         )
    #
    #     return value
