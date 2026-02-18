from dataclasses import asdict, is_dataclass, dataclass
from typing import Optional, Literal, List


class BaseDTOMixin:
    @classmethod
    def _from_orm(cls, obj):
        if obj:
            instance_data = {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
            return cls(**instance_data)
        return None

    @classmethod
    def to_application(cls, obj):
        return cls._from_orm(obj)

    def to_payload(self, exclude_none: bool = True) -> dict:
        data = asdict(self) if is_dataclass(self) else dict(self)
        return {k: v for k, v in data.items() if not (exclude_none and v is None)}


@dataclass
class SortDTO:
    sort_by: Optional[str] = None
    order: Optional[Literal["asc", "desc"]] = "asc"


@dataclass
class PaginationDTO:
    page: Optional[int] = None
    per_page: Optional[int] = None
    total: Optional[int] = None
    items: Optional[List[BaseDTOMixin]] = None