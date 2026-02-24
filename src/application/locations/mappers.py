from sqlalchemy import inspect
from sqlalchemy.orm.attributes import NO_VALUE

from src.application.locations.dtos import CountryDTO, CityDTO
from src.application.locations.models import Country, City


def country_orm_to_dto(row: Country) -> CountryDTO:
    return CountryDTO(
        id=row.id,
        name=row.name,
    )

def city_orm_to_dto(
    row: City,
    populate_country: bool = False,
) -> CityDTO:

    country_dto = None

    if populate_country:
        state = inspect(row)
        country_loaded = state.attrs.country.loaded_value

        if country_loaded is not None and not country_loaded is NO_VALUE:
            country_dto = country_orm_to_dto(country_loaded)

    return CityDTO(
        id=row.id,
        name=row.name,
        country_id=row.country_id,
        country=country_dto,
    )