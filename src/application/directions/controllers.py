from typing import List, Optional

from fastapi import HTTPException, status as s

from src.application.directions.dtos import SalaryDTO, DirectionDTO
from src.application.directions.interfaces import (
    IDirectionSalaryController,
    ISalaryRepository,
    IDirectionRepository,
    IDirectionSearchService,
)
from src.application.locations.interfaces import ICityRepository
from src.domain.interfaces import IOpenAIService, IUoW
from src.domain.value_objects import ChatGPTModel
from src.domain.base_dto import PaginationDTO


class DirectionSalaryController(IDirectionSalaryController):

    def __init__(
            self,
            salary_repository: ISalaryRepository,
            direction_repository: IDirectionRepository,
            city_repository: ICityRepository,
            uow: IUoW,
            openai_service: IOpenAIService,
            direction_search_service: IDirectionSearchService,
    ):
        self._salary_repository = salary_repository
        self._direction_repository = direction_repository
        self._city_repository = city_repository
        self._uow = uow
        self._openai_service = openai_service
        self._direction_search_service = direction_search_service

    async def get_ai_directions(
            self,
            skills: List[str],
            city_id: int,
    ) -> List[SalaryDTO]:
        city = await self._city_repository.get_by_id(city_id, True)

        if not city:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="City not found")

        res = await self._openai_service.get_specializations(
            skills=skills,
            city=city.name,
            country=city.country.name,
            model=ChatGPTModel.GPT_4_1
        )

        result = []

        for item in res:

            item.city_id = city.id

            # 1️⃣ Проверяем direction
            direction = await self._direction_repository.get_by_name(item.direction.name)

            if not direction:
                async with self._uow:
                    direction = await self._direction_repository.add(item.direction)

            # теперь direction гарантированно существует
            item.direction_id = direction.id

            # 2️⃣ Проверяем salary
            existing_salary = await self._salary_repository.get_by_city_and_direction(
                city.id,
                direction.id
            )

            if not existing_salary:
                async with self._uow:
                    saved_salary = await self._salary_repository.add(item)
            else:
                saved_salary = existing_salary

            saved_salary.direction = direction
            result.append(saved_salary)

        return result

    async def direction_autocomplete(
            self,
            pagination: PaginationDTO[DirectionDTO],
            q: Optional[str] = None,
    ) -> PaginationDTO[DirectionDTO]:
        count = await self._direction_search_service.count()

        if count < 1:
            total = await self._direction_repository.get()
            total = total.total

            directions = await self._direction_repository.get(
                pagination=PaginationDTO[DirectionDTO](per_page=total)
            )
            directions = directions.items

            await self._direction_search_service.bulk_index(directions)

        res = await self._direction_search_service.search(pagination=pagination, name=q)
        return res
