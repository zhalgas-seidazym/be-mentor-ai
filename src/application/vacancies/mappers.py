from typing import Optional

from sqlalchemy import inspect
from sqlalchemy.orm import NO_VALUE

from src.application.vacancies.dtos import VacancyDTO, VacancySkillDTO, UserVacancyDTO
from src.application.vacancies.models import Vacancy, VacancySkill, UserVacancy
from src.application.skills.mappers import skill_orm_to_dto


def vacancy_orm_to_dto(row: Vacancy) -> Optional[VacancyDTO]:
    return VacancyDTO(
        id=row.id,
        title=row.title,
        direction_id=row.direction_id,
        city_id=row.city_id,
        salary_amount=float(row.salary_amount) if row.salary_amount is not None else None,
        salary_currency=row.salary_currency,
        vacancy_type=row.vacancy_type,
        url=row.url,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def vacancy_dto_to_orm(dto: VacancyDTO, row: Optional[Vacancy] = None) -> Vacancy:
    row = row or Vacancy()

    if dto.id is not None:
        row.id = dto.id

    if dto.title is not None:
        row.title = dto.title

    if dto.direction_id is not None:
        row.direction_id = dto.direction_id

    if dto.city_id is not None:
        row.city_id = dto.city_id

    if dto.salary_amount is not None:
        row.salary_amount = dto.salary_amount

    if dto.salary_currency is not None:
        row.salary_currency = dto.salary_currency

    if dto.vacancy_type is not None:
        row.vacancy_type = dto.vacancy_type

    if dto.url is not None:
        row.url = dto.url

    return row


def vacancy_skill_orm_to_dto(
    row: VacancySkill,
    populate_skill: bool = False,
) -> Optional[VacancySkillDTO]:
    skill_dto = None

    if populate_skill:
        state = inspect(row)
        skill_loaded = state.attrs.skill.loaded_value

        if skill_loaded is not None and skill_loaded is not NO_VALUE:
            skill_dto = skill_orm_to_dto(skill_loaded)

    return VacancySkillDTO(
        vacancy_id=row.vacancy_id,
        skill_id=row.skill_id,
        skill=skill_dto,
    )


def vacancy_skill_dto_to_orm(
    dto: VacancySkillDTO,
    row: Optional[VacancySkill] = None,
) -> VacancySkill:
    row = row or VacancySkill()

    if dto.vacancy_id is not None:
        row.vacancy_id = dto.vacancy_id

    if dto.skill_id is not None:
        row.skill_id = dto.skill_id

    return row


def user_vacancy_orm_to_dto(
    row: UserVacancy,
    populate_vacancy: bool = False,
) -> Optional[UserVacancyDTO]:
    vacancy_dto = None

    if populate_vacancy:
        state = inspect(row)
        vacancy_loaded = state.attrs.vacancy.loaded_value

        if vacancy_loaded is not None and vacancy_loaded is not NO_VALUE:
            vacancy_dto = vacancy_orm_to_dto(vacancy_loaded)

    return UserVacancyDTO(
        user_id=row.user_id,
        vacancy_id=row.vacancy_id,
        vacancy=vacancy_dto,
    )


def user_vacancy_dto_to_orm(
    dto: UserVacancyDTO,
    row: Optional[UserVacancy] = None,
) -> UserVacancy:
    row = row or UserVacancy()

    if dto.user_id is not None:
        row.user_id = dto.user_id

    if dto.vacancy_id is not None:
        row.vacancy_id = dto.vacancy_id

    return row
