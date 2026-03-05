from typing import Optional

from sqlalchemy import inspect
from sqlalchemy.orm import NO_VALUE

from src.application.directions.mappers import direction_orm_to_dto
from src.application.locations.mappers import city_orm_to_dto
from src.application.skills.mappers import user_skill_orm_to_dto
from src.application.users.dtos import UserDTO
from src.application.users.models import User


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
        current_streak=row.current_streak,
        longest_streak=row.longest_streak,
        last_interview_day=row.last_interview_day,
        timezone=row.timezone,
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
        "current_streak": dto.current_streak,
        "longest_streak": dto.longest_streak,
        "last_interview_day": dto.last_interview_day,
        "timezone": dto.timezone,
    }

    for field, value in updates.items():
        if value is not None:
            setattr(row, field, value)

    return row

