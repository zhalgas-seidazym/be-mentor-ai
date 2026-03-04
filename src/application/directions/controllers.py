from typing import List, Optional

from fastapi import HTTPException, status as s

from src.application.directions.dtos import SalaryDTO, DirectionDTO, ProgressStatisticsDTO
from src.application.users.dtos import UserDTO
from src.application.directions.interfaces import (
    IDirectionSalaryController,
    ISalaryRepository,
    IDirectionRepository,
    IDirectionSearchService,
    IDirectionStatisticsService,
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
            direction_statistics_service: IDirectionStatisticsService,
    ):
        self._salary_repository = salary_repository
        self._direction_repository = direction_repository
        self._city_repository = city_repository
        self._uow = uow
        self._openai_service = openai_service
        self._direction_search_service = direction_search_service
        self._direction_statistics_service = direction_statistics_service

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

            direction = await self._direction_repository.get_by_name(item.direction.name)

            if not direction:
                async with self._uow:
                    direction = await self._direction_repository.add(item.direction)

            item.direction_id = direction.id

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

    async def create_direction(
            self,
            name: str,
    ) -> DirectionDTO:
        existing = await self._direction_repository.get_by_name(name)

        if existing:
            raise HTTPException(
                status_code=s.HTTP_409_CONFLICT,
                detail=f"Direction {name} already exists"
            )

        description = ""
        for _ in range(3):
            description = await self._openai_service.get_direction_description(
                direction_name=name,
                model=ChatGPTModel.GPT_4_1,
            )
            if description:
                break
        if not description:
            raise HTTPException(
                status_code=s.HTTP_408_REQUEST_TIMEOUT,
                detail="Failed to generate description, please try again"
            )

        direction = DirectionDTO(
            name=name,
            description=description,
        )

        async with self._uow:
            direction = await self._direction_repository.add(direction)

        await self._direction_search_service.index(
            direction_id=direction.id,
            name=direction.name,
        )

        return direction

    async def get_by_id(
            self,
            direction_id: int,
    ) -> Optional[DirectionDTO]:
        res = await self._direction_repository.get_by_id(direction_id)
        if res is None:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=f"Direction {direction_id} not found")
        return res

    async def get_my_statistics(
            self,
            user_id: int,
    ) -> ProgressStatisticsDTO:
        return await self._direction_statistics_service.get_statistics(user_id=user_id)

    async def get_my_salary(
            self,
            user: UserDTO,
    ) -> Optional[SalaryDTO]:
        if not user.city_id or not user.direction_id:
            raise HTTPException(status_code=s.HTTP_400_BAD_REQUEST, detail="User city_id or direction_id not set")

        city_id = user.city_id
        direction_id = user.direction_id

        salary = await self._salary_repository.get_by_city_and_direction(
            city_id=city_id,
            direction_id=direction_id,
            populate_city=True,
            populate_direction=True,
        )
        if salary is not None:
            return salary

        city = await self._city_repository.get_by_id(city_id, populate_country=True)
        if not city:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=f"City {city_id} not found")
        if not city.country or not city.country.name:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="City country not found")

        direction = await self._direction_repository.get_by_id(direction_id)
        if not direction:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=f"Direction {direction_id} not found")

        ai_salary = await self._openai_service.get_direction_salary(
            country=city.country.name,
            city=city.name or "",
            direction=direction.name or "",
            model=ChatGPTModel.GPT_4_1,
        )
        if not ai_salary:
            raise HTTPException(
                status_code=s.HTTP_408_REQUEST_TIMEOUT,
                detail="Failed to generate salary, please try again"
            )

        async with self._uow:
            await self._salary_repository.add(
                SalaryDTO(
                    city_id=city_id,
                    direction_id=direction_id,
                    amount=ai_salary["amount"],
                    currency=ai_salary["currency"],
                )
            )

        salary = await self._salary_repository.get_by_city_and_direction(
            city_id=city_id,
            direction_id=direction_id,
            populate_city=True,
            populate_direction=True,
        )
        if salary is None:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="Salary not found")
        return salary
