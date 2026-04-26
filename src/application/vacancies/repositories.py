from typing import Optional, List

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.application.vacancies.dtos import VacancyDTO, VacancySkillDTO, UserVacancyDTO
from src.application.vacancies.interfaces import (
    IVacancyRepository,
    IVacancySkillRepository,
    IUserVacancyRepository,
)
from src.application.vacancies.models import Vacancy, VacancySkill, UserVacancy
from src.application.vacancies.mappers import (
    vacancy_orm_to_dto,
    vacancy_dto_to_orm,
    vacancy_skill_orm_to_dto,
    vacancy_skill_dto_to_orm,
    user_vacancy_orm_to_dto,
    user_vacancy_dto_to_orm,
)
from src.domain.base_dto import PaginationDTO


class VacancyRepository(IVacancyRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    def _base_query(
        self,
        populate_skills: bool = False,
        populate_city: bool = False,
        populate_direction: bool = False,
    ):
        query = select(Vacancy)
        if populate_skills:
            query = query.options(
                selectinload(Vacancy.vacancy_skills).selectinload(VacancySkill.skill)
            )
        if populate_city:
            query = query.options(selectinload(Vacancy.city))
        if populate_direction:
            query = query.options(selectinload(Vacancy.direction))
        return query

    async def _fetch_one(self, query) -> Optional[VacancyDTO]:
        result = await self._session.execute(query)
        row = result.scalars().first()
        return vacancy_orm_to_dto(row) if row else None

    async def add(self, dto: VacancyDTO) -> Optional[VacancyDTO]:
        row = vacancy_dto_to_orm(dto)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return vacancy_orm_to_dto(row)

    async def get_by_id(
        self,
        vacancy_id: int,
        populate_skills: bool = False,
        populate_city: bool = False,
        populate_direction: bool = False,
    ) -> Optional[VacancyDTO]:
        query = self._base_query(
            populate_skills=populate_skills,
            populate_city=populate_city,
            populate_direction=populate_direction,
        )
        query = query.where(Vacancy.id == vacancy_id)
        result = await self._session.execute(query)
        row = result.scalars().first()
        if not row:
            return None
        return vacancy_orm_to_dto(
            row,
            populate_skills=populate_skills,
            populate_city=populate_city,
            populate_direction=populate_direction,
        )

    async def get(
        self,
        pagination: Optional[PaginationDTO[VacancyDTO]] = None,
        direction_id: Optional[int] = None,
        city_id: Optional[int] = None,
        q: Optional[str] = None,
    ) -> PaginationDTO[VacancyDTO]:
        base_query = self._base_query()

        if direction_id is not None:
            base_query = base_query.where(Vacancy.direction_id == direction_id)

        if city_id is not None:
            base_query = base_query.where(Vacancy.city_id == city_id)

        if q:
            base_query = base_query.where(Vacancy.title.ilike(f"%{q}%"))

        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await self._session.execute(count_query)
        total = count_result.scalar_one()

        if pagination is None or pagination.per_page is None:
            query = base_query
            page = 1
            per_page = total
        else:
            page = max(pagination.page or 1, 1)
            per_page = max(pagination.per_page or 10, 1)
            offset = (page - 1) * per_page
            query = base_query.offset(offset).limit(per_page)

        result = await self._session.execute(query)
        rows = result.scalars().all()
        items = [vacancy_orm_to_dto(row) for row in rows]

        return PaginationDTO[VacancyDTO](
            page=page,
            per_page=per_page,
            total=total,
            items=items,
        )

    async def update(self, vacancy_id: int, dto: VacancyDTO) -> Optional[VacancyDTO]:
        query = self._base_query().where(Vacancy.id == vacancy_id)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return None

        row = vacancy_dto_to_orm(dto, row)
        await self._session.flush()
        await self._session.refresh(row)
        return vacancy_orm_to_dto(row)

    async def delete(self, vacancy_id: int) -> bool:
        query = self._base_query().where(Vacancy.id == vacancy_id)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return False

        await self._session.delete(row)
        return True


class VacancySkillRepository(IVacancySkillRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    def _base_query(self, populate_skill: bool = False):
        query = select(VacancySkill)
        if populate_skill:
            query = query.options(selectinload(VacancySkill.skill))
        return query

    async def add(self, dto: VacancySkillDTO) -> Optional[VacancySkillDTO]:
        row = vacancy_skill_dto_to_orm(dto)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return vacancy_skill_orm_to_dto(row)

    async def add_many(self, dtos: List[VacancySkillDTO]) -> List[VacancySkillDTO]:
        rows = [vacancy_skill_dto_to_orm(dto) for dto in dtos]
        self._session.add_all(rows)
        await self._session.flush()
        for row in rows:
            await self._session.refresh(row)
        return [vacancy_skill_orm_to_dto(row) for row in rows]

    async def get_by_vacancy_id(
        self,
        vacancy_id: int,
        populate_skill: bool = False,
    ) -> List[VacancySkillDTO]:
        query = self._base_query(populate_skill).where(VacancySkill.vacancy_id == vacancy_id)
        result = await self._session.execute(query)
        rows = result.scalars().all()
        return [vacancy_skill_orm_to_dto(row, populate_skill=populate_skill) for row in rows]

    async def get_by_vacancy_and_skill(
        self,
        vacancy_id: int,
        skill_id: int,
        populate_skill: bool = False,
    ) -> Optional[VacancySkillDTO]:
        query = self._base_query(populate_skill).where(
            VacancySkill.vacancy_id == vacancy_id,
            VacancySkill.skill_id == skill_id,
        )
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()
        return vacancy_skill_orm_to_dto(row, populate_skill=populate_skill) if row else None

    async def delete(self, vacancy_id: int, skill_id: int) -> bool:
        query = select(VacancySkill).where(
            VacancySkill.vacancy_id == vacancy_id,
            VacancySkill.skill_id == skill_id,
        )
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return False

        await self._session.delete(row)
        return True


class UserVacancyRepository(IUserVacancyRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    def _base_query(self, populate_vacancy: bool = False):
        query = select(UserVacancy)
        if populate_vacancy:
            query = query.options(selectinload(UserVacancy.vacancy))
        return query

    async def add(self, dto: UserVacancyDTO) -> Optional[UserVacancyDTO]:
        row = user_vacancy_dto_to_orm(dto)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return user_vacancy_orm_to_dto(row)

    async def add_many(self, dtos: List[UserVacancyDTO]) -> List[UserVacancyDTO]:
        rows = [user_vacancy_dto_to_orm(dto) for dto in dtos]
        self._session.add_all(rows)
        await self._session.flush()
        for row in rows:
            await self._session.refresh(row)
        return [user_vacancy_orm_to_dto(row) for row in rows]

    async def get_by_user_id(
        self,
        user_id: int,
        populate_vacancy: bool = False,
    ) -> List[UserVacancyDTO]:
        query = self._base_query(populate_vacancy).where(UserVacancy.user_id == user_id)
        result = await self._session.execute(query)
        rows = result.scalars().all()
        return [user_vacancy_orm_to_dto(row, populate_vacancy=populate_vacancy) for row in rows]

    async def get_by_user_and_vacancy(
        self,
        user_id: int,
        vacancy_id: int,
        populate_vacancy: bool = False,
    ) -> Optional[UserVacancyDTO]:
        query = self._base_query(populate_vacancy).where(
            UserVacancy.user_id == user_id,
            UserVacancy.vacancy_id == vacancy_id,
        )
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()
        return user_vacancy_orm_to_dto(row, populate_vacancy=populate_vacancy) if row else None

    async def delete(self, user_id: int, vacancy_id: int) -> bool:
        query = select(UserVacancy).where(
            UserVacancy.user_id == user_id,
            UserVacancy.vacancy_id == vacancy_id,
        )
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return False

        await self._session.delete(row)
        return True

    async def delete_by_user(self, user_id: int) -> int:
        result = await self._session.execute(
            delete(UserVacancy).where(UserVacancy.user_id == user_id)
        )
        return int(result.rowcount or 0)
