import re
from inspect import Signature, Parameter
from typing import Any, Optional, Literal, List

from fastapi import Form, Query, HTTPException, status
from pydantic import BaseModel, Field, field_validator


class BaseSchema(BaseModel):
    @classmethod
    def as_form(cls):
        params = []
        for name, field in cls.model_fields.items():
            annotation = field.annotation
            default: Any = ... if field.is_required() else field.default
            params.append(
                Parameter(
                    name,
                    Parameter.POSITIONAL_OR_KEYWORD,
                    default=Form(default),
                    annotation=annotation,
                )
            )

        async def _as_form(**data):
            return cls(**data)

        _as_form.__signature__ = Signature(
            parameters=params,
            return_annotation=cls,
        )
        return _as_form

    @classmethod
    def as_query(cls):
        params = []
        for name, field in cls.model_fields.items():
            annotation = field.annotation
            default: Any = ... if field.is_required() else field.default
            params.append(
                Parameter(
                    name,
                    Parameter.POSITIONAL_OR_KEYWORD,
                    default=Query(default),
                    annotation=annotation,
                )
            )

        async def _as_query(**data):
            return cls(**data)

        _as_query.__signature__ = Signature(
            parameters=params,
            return_annotation=cls,
        )
        return _as_query

class PasswordSchema(BaseModel):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$"

        if not re.match(pattern, value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long and contain one uppercase letter, one lowercase letter, and one digit"
            )

        return value

class SortSchema(BaseSchema):
    sort_by: str
    order: Optional[Literal["asc", "desc"]] = "asc"


class PaginationSchema(BaseSchema):
    page: int = 1
    per_page: int = 10
    total: Optional[int] = None