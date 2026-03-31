from typing import Dict, List, Union

from fastapi import HTTPException, status as s
from redis.asyncio import Redis

from src.application.vacancies.dtos import UserVacancyDTO, VacancyDTO, VacancySkillDTO
from src.application.vacancies.interfaces import (
    IVacancyController,
    IUserVacancyRepository,
    IVacancyRepository,
    IVacancySkillRepository,
)
from src.infrastructure.integrations.airflow_client import AirflowClient


class VacancyController(IVacancyController):
    def __init__(
        self,
        vacancy_repository: IVacancyRepository,
        vacancy_skill_repository: IVacancySkillRepository,
        user_vacancy_repository: IUserVacancyRepository,
        airflow_client: AirflowClient,
        redis: Redis,
    ):
        self._vacancy_repository = vacancy_repository
        self._vacancy_skill_repository = vacancy_skill_repository
        self._user_vacancy_repository = user_vacancy_repository
        self._airflow_client = airflow_client
        self._redis = redis

    async def get_my_vacancies(
        self,
        user_id: int,
        populate_vacancy: bool = False,
    ) -> Union[List[UserVacancyDTO], Dict[str, Union[str, int]]]:
        items = await self._user_vacancy_repository.get_by_user_id(
            user_id=user_id,
            populate_vacancy=populate_vacancy,
        )
        if not items:
            redis_key = f"vacancy_search_in_progress:{user_id}"
            # Set once (NX) with TTL to avoid re-triggering frequently.
            is_first = await self._redis.set(redis_key, "1", ex=600, nx=True)
            if is_first:
                try:
                    await self._airflow_client.trigger_dag(
                        dag_id="vacancy_pipeline_orchestrator_dag",
                        conf={"user_id": user_id},
                    )
                except Exception:
                    # Best-effort: do not block the request if Airflow is down.
                    pass
            ttl = await self._redis.ttl(redis_key)
            if ttl is None or ttl <= 0:
                ttl = 600
            return {"detail": "Поиск вакансий уже идет", "retry_after": int(ttl)}
        return items

    async def get_by_id(
        self,
        vacancy_id: int,
        populate_skills: bool = False,
        populate_city: bool = False,
        populate_direction: bool = False,
    ) -> VacancyDTO:
        vacancy = await self._vacancy_repository.get_by_id(
            vacancy_id=vacancy_id,
            populate_skills=populate_skills,
            populate_city=populate_city,
            populate_direction=populate_direction,
        )
        if vacancy is None:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="Vacancy not found")

        return vacancy

    async def get_vacancy_skills(
        self,
        vacancy_id: int,
        populate_skill: bool = False,
    ) -> List[VacancySkillDTO]:
        vacancy = await self._vacancy_repository.get_by_id(vacancy_id=vacancy_id)
        if vacancy is None:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="Vacancy not found")
        return await self._vacancy_skill_repository.get_by_vacancy_id(
            vacancy_id=vacancy_id,
            populate_skill=populate_skill,
        )
