from typing import Optional

from sqlalchemy import inspect
from sqlalchemy.orm import NO_VALUE

from src.application.directions.mappers import direction_orm_to_dto
from src.application.locations.mappers import city_orm_to_dto
from src.application.skills.mappers import skill_orm_to_dto
from src.application.users.dtos import UserDTO, UserSkillDTO
from src.application.users.models import User, UserSkill


def user_orm_to_dto(
    row: User,
    populate_city: bool = False,
    populate_skills: bool = False,
    populate_direction: bool = False,
) -> Optional[UserDTO]:

    state = inspect(row)

    city_dto = None
    skills_dto = None
    modules_dto = None
    direction_dto = None

    # --- City ---
    if populate_city:
        city_loaded = state.attrs.city.loaded_value
        if city_loaded is not None and city_loaded is not NO_VALUE:
            city_dto = city_orm_to_dto(city_loaded)

    # --- Direction ---
    if populate_direction:
        direction_loaded = state.attrs.direction.loaded_value
        if direction_loaded is not None and direction_loaded is not NO_VALUE:
            direction_dto = direction_orm_to_dto(direction_loaded)

    # --- Skills ---
    if populate_skills:
        skills_loaded = state.attrs.user_skills.loaded_value

        if skills_loaded is not NO_VALUE:
            skills_dto = []
            modules_dto = []

            for us in skills_loaded:
                dto = user_skill_orm_to_dto(
                    us,
                    populate_skill=True,
                )
                if dto is None:
                    continue

                if dto.to_learn:
                    modules_dto.append(dto)
                else:
                    skills_dto.append(dto)

    return UserDTO(
        id=row.id,
        email=row.email,
        password=row.password,
        name=row.name,
        city_id=row.city_id,
        direction_id=row.direction_id,
        is_onboarding_completed=row.is_onboarding_completed,
        skills=skills_dto,
        modules=modules_dto,
        direction=direction_dto,
        city=city_dto,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )

def user_dto_to_orm(
    dto: UserDTO,
    row: Optional[User] = None,
) -> User:

    row = row or User()

    if dto.id is not None:
        row.id = dto.id

    updates = {
        "email": dto.email,
        "password": dto.password,
        "name": dto.name,
        "city_id": dto.city_id,
        "direction_id": dto.direction_id,
        "is_onboarding_completed": dto.is_onboarding_completed,
    }

    for field, value in updates.items():
        if value is not None:
            setattr(row, field, value)

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

    return row
