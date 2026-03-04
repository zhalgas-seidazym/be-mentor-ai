from typing import Optional

from sqlalchemy import inspect
from sqlalchemy.orm import NO_VALUE

from src.application.skills.dtos import SkillDTO, UserSkillDTO
from src.application.skills.models import Skill, UserSkill


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


def user_skill_orm_to_dto(
    row: UserSkill,
    populate_skill: bool = False,
) -> Optional[UserSkillDTO]:

    skill_dto = None

    if populate_skill:
        state = inspect(row)
        skill_loaded = state.attrs.skill.loaded_value

        if skill_loaded is not None and skill_loaded is not NO_VALUE:
            skill_dto = skill_orm_to_dto(skill_loaded)

    return UserSkillDTO(
        user_id=row.user_id,
        skill_id=row.skill_id,
        skill=skill_dto,
        to_learn=row.to_learn,
        match_percentage=row.match_percentage,
    )


def user_skill_dto_to_orm(
    dto: UserSkillDTO,
    row: Optional[UserSkill] = None,
) -> UserSkill:

    row = row or UserSkill()

    if dto.user_id is not None:
        row.user_id = dto.user_id

    if dto.skill_id is not None:
        row.skill_id = dto.skill_id

    if dto.to_learn is not None:
        row.to_learn = dto.to_learn

    if dto.match_percentage is not None:
        row.match_percentage = dto.match_percentage

    return row
