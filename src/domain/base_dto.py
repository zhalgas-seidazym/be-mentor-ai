from dataclasses import asdict, is_dataclass, dataclass, fields
from typing import Optional, Literal, List


class BaseDTOMixin:
    @classmethod
    def _from_orm(cls, obj):
        if not obj:
            return None

        dto_fields = {f.name for f in fields(cls)}
        instance_data = {
            k: v
            for k, v in obj.__dict__.items()
            if k in dto_fields
        }

        return cls(**instance_data)

    @classmethod
    def to_application(cls, obj):
        return cls._from_orm(obj)

    def to_payload(self, exclude_none: bool = True) -> dict:
        data = asdict(self) if is_dataclass(self) else dict(self)
        return {k: v for k, v in data.items() if not (exclude_none and v is None)}


from dataclasses import asdict, is_dataclass, dataclass, fields
from typing import Optional, Literal, List, TypeVar, Generic


@dataclass
class SortDTO:
    sort_by: Optional[str] = None
    order: Optional[Literal["asc", "desc"]] = "asc"


T = TypeVar("T")

@dataclass
class PaginationDTO(Generic[T]):
    page: Optional[int] = None
    per_page: Optional[int] = None
    total: Optional[int] = None
    items: Optional[List[T]] = None