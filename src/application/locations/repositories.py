from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.application.locations.interfaces import ICountryRepository, ICityRepository
from src.application.locations.models import Country, City
from src.application.locations.dtos import CountryDTO, CityDTO
from src.application.locations.mappers import country_orm_to_dto, city_orm_to_dto
from src.domain.base_dto import PaginationDTO


class CountryRepository(ICountryRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    def _base_query(self):
        return select(Country)

    async def _fetch_one(self, query) -> Optional[CountryDTO]:
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()
        return country_orm_to_dto(row) if row else None

    async def get_by_id(self, country_id: int) -> Optional[CountryDTO]:
        query = self._base_query().where(Country.id == country_id)
        return await self._fetch_one(query)

    async def get_by_name(self, name: str) -> Optional[CountryDTO]:
        query = self._base_query().where(Country.name == name)
        return await self._fetch_one(query)

    async def get(
        self,
        name: Optional[str] = None,
        pagination: Optional[PaginationDTO[CountryDTO]] = None,
    ) -> PaginationDTO[CountryDTO]:

        pagination = pagination or PaginationDTO[CountryDTO]()

        page = max(pagination.page or 1, 1)
        per_page = max(pagination.per_page or 10, 1)
        offset = (page - 1) * per_page

        base_query = self._base_query()

        if name:
            base_query = base_query.where(
                Country.name.ilike(f"%{name}%")
            )

        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await self._session.execute(count_query)
        total = count_result.scalar_one()

        query = base_query.offset(offset).limit(per_page)
        result = await self._session.execute(query)
        rows = result.scalars().all()

        items: List[CountryDTO] = [
            country_orm_to_dto(row) for row in rows
        ]

        return PaginationDTO[CountryDTO](
            page=page,
            per_page=per_page,
            total=total,
            items=items,
        )


class CityRepository(ICityRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    def _base_query(self, populate_country: bool = False):
        query = select(City)

        if populate_country:
            query = query.options(
                selectinload(City.country)
            )

        return query

    async def _fetch_one(self, query, populate_country: bool) -> Optional[CityDTO]:
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return None

        return city_orm_to_dto(row, populate_country=populate_country)

    async def get_by_id(
        self,
        city_id: int,
        populate_country: bool = False,
    ) -> Optional[CityDTO]:

        query = self._base_query(populate_country).where(City.id == city_id)
        return await self._fetch_one(query, populate_country)

    async def get_by_name(
        self,
        name: str,
        populate_country: bool = False,
    ) -> Optional[CityDTO]:

        query = self._base_query(populate_country).where(City.name == name)
        return await self._fetch_one(query, populate_country)

    async def get(
        self,
        name: Optional[str] = None,
        country_id: Optional[int] = None,
        pagination: Optional[PaginationDTO[CityDTO]] = None,
        populate_country: bool = False,
    ) -> PaginationDTO[CityDTO]:

        pagination = pagination or PaginationDTO[CityDTO]()

        page = max(pagination.page or 1, 1)
        per_page = max(pagination.per_page or 10, 1)
        offset = (page - 1) * per_page

        base_query = self._base_query(populate_country)

        if name:
            base_query = base_query.where(
                City.name.ilike(f"%{name}%")
            )

        if country_id:
            base_query = base_query.where(
                City.country_id == country_id
            )

        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await self._session.execute(count_query)
        total = count_result.scalar_one()

        query = base_query.offset(offset).limit(per_page)
        result = await self._session.execute(query)
        rows = result.scalars().all()

        items: List[CityDTO] = [
            city_orm_to_dto(row, populate_country=populate_country)
            for row in rows
        ]

        return PaginationDTO[CityDTO](
            page=page,
            per_page=per_page,
            total=total,
            items=items,
        )