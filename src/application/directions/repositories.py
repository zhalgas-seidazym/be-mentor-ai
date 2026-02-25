from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.application.directions.dtos import SalaryDTO, DirectionDTO
from src.application.directions.interfaces import ISalaryRepository, IDirectionRepository
from src.application.directions.mappers import salary_orm_to_dto, salary_dto_to_orm, direction_orm_to_dto, \
    direction_dto_to_orm
from src.application.directions.models import Salary, Direction
from src.domain.base_dto import PaginationDTO


class DirectionRepository(IDirectionRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    def _base_query(self):
        return select(Direction)

    async def get_by_id(
        self,
        direction_id: int,
    ) -> Optional[DirectionDTO]:

        query = self._base_query().where(
            Direction.id == direction_id
        )

        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        return direction_orm_to_dto(row) if row else None

    async def get_by_name(
        self,
        name: str,
    ) -> Optional[DirectionDTO]:

        query = self._base_query().where(
            Direction.name.ilike(name)
        )

        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        return direction_orm_to_dto(row) if row else None

    async def get(
            self,
            name: Optional[str] = None,
            pagination: Optional[PaginationDTO[DirectionDTO]] = None,
    ) -> PaginationDTO[DirectionDTO]:
        pagination = pagination or PaginationDTO[DirectionDTO]()

        page = max(pagination.page or 1, 1)
        per_page = max(pagination.per_page or 10, 1)
        offset = (page - 1) * per_page

        base_query = self._base_query()

        # --- filter ---
        if name:
            base_query = base_query.where(
                Direction.name.ilike(f"%{name}%")
            )

        # --- total count ---
        count_query = select(func.count()).select_from(
            base_query.subquery()
        )
        count_result = await self._session.execute(count_query)
        total = count_result.scalar_one()

        # --- pagination ---
        query = base_query.offset(offset).limit(per_page)
        result = await self._session.execute(query)
        rows = result.scalars().all()

        items: List[DirectionDTO] = [
            direction_orm_to_dto(row)
            for row in rows
        ]

        return PaginationDTO[DirectionDTO](
            page=page,
            per_page=per_page,
            total=total,
            items=items,
        )

    async def add(
        self,
        dto: DirectionDTO,
    ) -> Optional[DirectionDTO]:

        row = direction_dto_to_orm(dto)

        self._session.add(row)

        await self._session.flush()
        await self._session.refresh(row)

        return direction_orm_to_dto(row)

    async def update(
        self,
        direction_id: int,
        dto: DirectionDTO,
    ) -> Optional[DirectionDTO]:

        query = select(Direction).where(
            Direction.id == direction_id
        )

        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return None

        row = direction_dto_to_orm(dto, row)

        await self._session.flush()
        await self._session.refresh(row)

        return direction_orm_to_dto(row)

    async def delete(
        self,
        direction_id: int,
    ) -> bool:

        query = select(Direction).where(
            Direction.id == direction_id
        )

        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return False

        await self._session.delete(row)
        return True

class SalaryRepository(ISalaryRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    def _base_query(
        self,
        populate_city: bool = False,
        populate_direction: bool = False,
    ):
        query = select(Salary)

        if populate_city:
            query = query.options(
                selectinload(Salary.city)
            )

        if populate_direction:
            query = query.options(
                selectinload(Salary.direction)
            )

        return query

    async def get(
        self,
        city_id: Optional[int] = None,
        direction_id: Optional[int] = None,
        pagination: Optional[PaginationDTO[SalaryDTO]] = None,
        populate_city: bool = False,
        populate_direction: bool = False,
    ) -> PaginationDTO[SalaryDTO]:

        pagination = pagination or PaginationDTO[SalaryDTO]()

        page = max(pagination.page or 1, 1)
        per_page = max(pagination.per_page or 10, 1)
        offset = (page - 1) * per_page

        base_query = self._base_query(
            populate_city=populate_city,
            populate_direction=populate_direction,
        )

        # --- filters ---
        if city_id is not None:
            base_query = base_query.where(
                Salary.city_id == city_id
            )

        if direction_id is not None:
            base_query = base_query.where(
                Salary.direction_id == direction_id
            )

        # --- total count ---
        count_query = select(func.count()).select_from(
            base_query.subquery()
        )
        count_result = await self._session.execute(count_query)
        total = count_result.scalar_one()

        # --- pagination ---
        query = base_query.offset(offset).limit(per_page)
        result = await self._session.execute(query)
        rows = result.scalars().all()

        items: List[SalaryDTO] = [
            salary_orm_to_dto(
                row,
                populate_city=populate_city,
                populate_direction=populate_direction,
            )
            for row in rows
        ]

        return PaginationDTO[SalaryDTO](
            page=page,
            per_page=per_page,
            total=total,
            items=items,
        )

    async def get_by_city_and_direction(
        self,
        city_id: int,
        direction_id: int,
        populate_city: bool = False,
        populate_direction: bool = False,
    ) -> Optional[SalaryDTO]:

        query = self._base_query(
            populate_city=populate_city,
            populate_direction=populate_direction,
        ).where(
            Salary.city_id == city_id,
            Salary.direction_id == direction_id,
        )

        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return None

        return salary_orm_to_dto(
            row,
            populate_city=populate_city,
            populate_direction=populate_direction,
        )

    async def add(
        self,
        dto: SalaryDTO,
    ) -> Optional[SalaryDTO]:

        row = salary_dto_to_orm(dto)

        self._session.add(row)

        await self._session.flush()
        await self._session.refresh(row)

        return salary_orm_to_dto(row)

    async def update(
        self,
        salary_id: int,
        dto: SalaryDTO,
    ) -> Optional[SalaryDTO]:

        query = select(Salary).where(Salary.id == salary_id)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return None

        row = salary_dto_to_orm(dto, row)

        await self._session.flush()
        await self._session.refresh(row)

        return salary_orm_to_dto(row)

    async def delete(
        self,
        salary_id: int,
    ) -> bool:

        query = select(Salary).where(Salary.id == salary_id)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return False

        await self._session.delete(row)
        return True