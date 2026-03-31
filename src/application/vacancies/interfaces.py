from abc import ABC, abstractmethod
from typing import Dict, Optional, List, Union

from src.application.vacancies.dtos import VacancyDTO, VacancySkillDTO, UserVacancyDTO
from src.domain.base_dto import PaginationDTO


class IVacancyRepository(ABC):
    @abstractmethod
    async def add(self, dto: VacancyDTO) -> Optional[VacancyDTO]: ...

    @abstractmethod
    async def get_by_id(
        self,
        vacancy_id: int,
        populate_skills: bool = False,
        populate_city: bool = False,
        populate_direction: bool = False,
    ) -> Optional[VacancyDTO]: ...

    @abstractmethod
    async def get(
        self,
        pagination: Optional[PaginationDTO[VacancyDTO]] = None,
        direction_id: Optional[int] = None,
        city_id: Optional[int] = None,
        q: Optional[str] = None,
    ) -> PaginationDTO[VacancyDTO]: ...

    @abstractmethod
    async def update(self, vacancy_id: int, dto: VacancyDTO) -> Optional[VacancyDTO]: ...

    @abstractmethod
    async def delete(self, vacancy_id: int) -> bool: ...


class IVacancySkillRepository(ABC):
    @abstractmethod
    async def add(self, dto: VacancySkillDTO) -> Optional[VacancySkillDTO]: ...

    @abstractmethod
    async def add_many(self, dtos: List[VacancySkillDTO]) -> List[VacancySkillDTO]: ...

    @abstractmethod
    async def get_by_vacancy_id(
        self,
        vacancy_id: int,
        populate_skill: bool = False,
    ) -> List[VacancySkillDTO]: ...

    @abstractmethod
    async def get_by_vacancy_and_skill(
        self,
        vacancy_id: int,
        skill_id: int,
        populate_skill: bool = False,
    ) -> Optional[VacancySkillDTO]: ...

    @abstractmethod
    async def delete(self, vacancy_id: int, skill_id: int) -> bool: ...


class IUserVacancyRepository(ABC):
    @abstractmethod
    async def add(self, dto: UserVacancyDTO) -> Optional[UserVacancyDTO]: ...

    @abstractmethod
    async def add_many(self, dtos: List[UserVacancyDTO]) -> List[UserVacancyDTO]: ...

    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: int,
        populate_vacancy: bool = False,
    ) -> List[UserVacancyDTO]: ...

    @abstractmethod
    async def get_by_user_and_vacancy(
        self,
        user_id: int,
        vacancy_id: int,
        populate_vacancy: bool = False,
    ) -> Optional[UserVacancyDTO]: ...

    @abstractmethod
    async def delete(self, user_id: int, vacancy_id: int) -> bool: ...


class IVacancyController(ABC):
    @abstractmethod
    async def get_my_vacancies(
        self,
        user_id: int,
        populate_vacancy: bool = False,
    ) -> Union[List[UserVacancyDTO], Dict[str, Union[str, int]]]: ...

    @abstractmethod
    async def get_by_id(
        self,
        vacancy_id: int,
        populate_skills: bool = False,
        populate_city: bool = False,
        populate_direction: bool = False,
    ) -> VacancyDTO: ...

    @abstractmethod
    async def get_vacancy_skills(
        self,
        vacancy_id: int,
        populate_skill: bool = False,
    ) -> List[VacancySkillDTO]: ...
