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