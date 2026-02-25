from typing import Optional

from sqlalchemy import inspect
from sqlalchemy.orm import NO_VALUE

from src.application.locations.mappers import city_orm_to_dto
from src.application.users.dtos import UserDTO
from src.application.users.models import User


def orm_to_dto(
    row: User,
    populate_city: bool = False,
) -> Optional[UserDTO]:

    city_dto = None

    if populate_city:
        state = inspect(row)
        city_loaded = state.attrs.city.loaded_value

        if city_loaded is not None and city_loaded is not NO_VALUE:
            city_dto = city_orm_to_dto(city_loaded)

    return UserDTO(
        id=row.id,
        email=row.email,
        password=row.password,
        name=row.name,
        is_onboarding_completed=row.is_onboarding_completed,
        city_id=row.city_id,
        city=city_dto,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )

def dto_to_orm(dto: UserDTO, row: Optional[User] = None) -> User:
    row = row or User()

    if dto.id is not None:
        row.id = dto.id

    updates = {
        "email": dto.email,
        "password": dto.password,
        "name": dto.name,
        "city_id": dto.city_id,
        "is_onboarding_completed": dto.is_onboarding_completed,
    }

    for field, value in updates.items():
        if value is not None:
            setattr(row, field, value)

    return row