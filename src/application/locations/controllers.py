from typing import Optional, Dict

from src.application.locations.dtos import CountryDTO
from src.application.locations.interfaces import ILocationController, ICountryRepository, ICityRepository
from src.domain.base_dto import PaginationDTO


class LocationController(ILocationController):
    def __init__(
            self,
            country_repository: ICountryRepository,
            city_repository: ICityRepository,
    ):
        self._country_repository = country_repository
        self._city_repository = city_repository

    async def get_countries_by_name(self, pagination: PaginationDTO[CountryDTO], q: Optional[str]) -> PaginationDTO[CountryDTO]:
        res = await self._country_repository.get(name=q, pagination=pagination)
        return res

    async def get_country_by_id(self, country_id: int) -> Optional[CountryDTO]:
        res = await self._country_repository.get_by_id(country_id)
        return res