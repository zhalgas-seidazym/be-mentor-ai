from typing import List

from fastapi import HTTPException, status as s

from src.application.vacancies.dtos import UserVacancyDTO, VacancyDTO, VacancySkillDTO
from src.application.vacancies.interfaces import (
    IVacancyController,
    IUserVacancyRepository,
    IVacancyRepository,
    IVacancySkillRepository,
)


class VacancyController(IVacancyController):
    def __init__(
        self,
        vacancy_repository: IVacancyRepository,
        vacancy_skill_repository: IVacancySkillRepository,
        user_vacancy_repository: IUserVacancyRepository,
    ):
        self._vacancy_repository = vacancy_repository
        self._vacancy_skill_repository = vacancy_skill_repository
        self._user_vacancy_repository = user_vacancy_repository

    async def get_my_vacancies(
        self,
        user_id: int,
        populate_vacancy: bool = False,
    ) -> List[UserVacancyDTO]:
        items = await self._user_vacancy_repository.get_by_user_id(
            user_id=user_id,
            populate_vacancy=populate_vacancy,
        )
        if not items:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="Vacancies not added yet")
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
