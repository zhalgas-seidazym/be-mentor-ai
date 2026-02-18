from dataclasses import dataclass
from typing import Optional, List

from src.domain.base_dto import BaseDTOMixin, PaginationDTO


@dataclass
class SkillDTO(BaseDTOMixin):
    id: Optional[int] = None
    name: Optional[str] = None


@dataclass
class PaginationSkillDTO(PaginationDTO):
    items: Optional[List[SkillDTO]] = None
