# directions/mappers.py
from typing import Optional

from sqlalchemy import inspect
from sqlalchemy.orm import NO_VALUE

from src.application.directions.dtos import DirectionDTO, SalaryDTO
from src.application.directions.models import Direction, Salary
from src.application.locations.mappers import city_orm_to_dto


def direction_orm_to_dto(row: Direction) -> Optional[DirectionDTO]:
    return DirectionDTO(
        id=row.id,
        name=row.name,
        description=row.description,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def direction_dto_to_orm(
    dto: DirectionDTO,
    row: Optional[Direction] = None,
) -> Direction:

    row = row or Direction()

    if dto.id is not None:
        row.id = dto.id

    if dto.name is not None:
        row.name = dto.name

    if dto.description is not None:
        row.description = dto.description

    return row


def salary_orm_to_dto(
    row: Salary,
    populate_city: bool = False,
    populate_direction: bool = False,
) -> Optional[SalaryDTO]:

    state = inspect(row)

    city_dto = None
    direction_dto = None

    # --- populate city ---
    if populate_city:
        city_loaded = state.attrs.city.loaded_value

        if city_loaded is not None and city_loaded is not NO_VALUE:
            city_dto = city_orm_to_dto(city_loaded)

    # --- populate direction ---
    if populate_direction:
        direction_loaded = state.attrs.direction.loaded_value

        if direction_loaded is not None and direction_loaded is not NO_VALUE:
            direction_dto = direction_orm_to_dto(direction_loaded)

    return SalaryDTO(
        id=row.id,
        direction_id=row.direction_id,
        city_id=row.city_id,
        amount=float(row.amount) if row.amount is not None else None,
        currency=row.currency,
        direction=direction_dto,
        city=city_dto,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )