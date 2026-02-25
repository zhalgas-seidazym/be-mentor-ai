from typing import Optional

from src.application.skills.dtos import SkillDTO
from src.application.skills.models import Skill


def skill_orm_to_dto(row: Skill) -> Optional[SkillDTO]:
    return SkillDTO(
        id=row.id,
        name=row.name,
    )


def skill_dto_to_orm(dto: SkillDTO, row: Optional[Skill] = None) -> Skill:
    row = row or Skill()

    if dto.id is not None:
        row.id = dto.id

    if dto.name is not None:
        row.name = dto.name

    return row