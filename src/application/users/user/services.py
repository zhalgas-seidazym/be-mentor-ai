from typing import Dict, Optional, List

from fastapi import HTTPException, status as s

from src.application.users.dtos import UserDTO
from src.application.users.interfaces import IUserRepository
from src.application.locations.interfaces import ICityRepository
from src.application.directions.interfaces import IDirectionRepository
from src.application.questions.interfaces import IUserQuestionRepository
from src.application.interview.interfaces import IInterviewSessionRepository, IInterviewQuestionRepository
from src.application.skills.dtos import SkillDTO, UserSkillDTO
from src.application.skills.interfaces import ISkillRepository, IUserSkillRepository
from src.application.questions.dtos import QuestionDTO
from src.application.questions.interfaces import IQuestionRepository
from src.application.directions.dtos import SalaryDTO, DirectionDTO
from src.application.directions.interfaces import ISalaryRepository
from src.domain.base_dto import PaginationDTO
from src.domain.interfaces import IUoW, IOpenAIService
from src.domain.value_objects import ChatGPTModel
from src.application.users.user.interfaces import IUserService


class UserService(IUserService):
    def __init__(
        self,
        uow: IUoW,
        user_repository: IUserRepository,
        user_skill_repository: IUserSkillRepository,
        skill_repository: ISkillRepository,
        question_repository: IQuestionRepository,
        user_question_repository: IUserQuestionRepository,
        interview_session_repository: IInterviewSessionRepository,
        interview_question_repository: IInterviewQuestionRepository,
        salary_repository: ISalaryRepository,
        city_repository: ICityRepository,
        direction_repository: IDirectionRepository,
        openai_service: IOpenAIService,
    ):
        self._uow = uow
        self._user_repository = user_repository
        self._user_skill_repository = user_skill_repository
        self._skill_repository = skill_repository
        self._question_repository = question_repository
        self._user_question_repository = user_question_repository
        self._interview_session_repository = interview_session_repository
        self._interview_question_repository = interview_question_repository
        self._salary_repository = salary_repository
        self._city_repository = city_repository
        self._direction_repository = direction_repository
        self._openai_service = openai_service

    async def get_theoretical_skills(
        self,
        direction_name: str,
        skill_names: List[str],
    ) -> List[UserSkillDTO]:
        return await self._openai_service.get_direction_theoretical_skills(
            direction_name=direction_name,
            skills=skill_names,
            model=ChatGPTModel.GPT_4_1,
        )

    async def create_profile(
        self,
        user_id: int,
        name: str,
        city_id: int,
        direction_id: int,
        timezone: str,
        unique_skill_ids: List[int],
        skill_name_list: List[str],
        ai_skills: List[UserSkillDTO],
        salary_context: Optional[Dict[str, str]] = None,
    ) -> UserDTO:
        skills_list: List[UserSkillDTO] = []
        modules_list: List[UserSkillDTO] = []

        async with self._uow:
            user = await self._update_user_profile(
                user_id=user_id,
                name=name,
                city_id=city_id,
                direction_id=direction_id,
                timezone=timezone,
            )
            if user is None:
                raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="User not found")

            if salary_context is not None:
                await self._create_salary_if_needed(
                    city_id=city_id,
                    direction_id=direction_id,
                    salary_context=salary_context,
                )

            skills_list = await self._attach_selected_skills(
                user_id=user_id,
                unique_skill_ids=unique_skill_ids,
            )

            modules_list = await self._attach_ai_skills_as_modules(
                user_id=user_id,
                ai_skills=ai_skills,
                existing_skill_names=skill_name_list,
                existing_skill_ids=unique_skill_ids,
            )

        user.name = name
        user.city_id = city_id
        user.direction_id = direction_id
        user.is_onboarding_completed = True
        user.skills = skills_list
        user.modules = modules_list
        return user

    async def attach_ai_skills_as_modules(
        self,
        user_id: int,
        ai_skills: List[UserSkillDTO],
        existing_skill_names: List[str],
        existing_skill_ids: List[int],
    ) -> List[UserSkillDTO]:
        return await self._attach_ai_skills_as_modules(
            user_id=user_id,
            ai_skills=ai_skills,
            existing_skill_names=existing_skill_names,
            existing_skill_ids=existing_skill_ids,
        )

    async def seed_questions_if_needed(
        self,
        module_id: int,
        canonical_name: str,
    ) -> None:
        await self._seed_questions_if_needed(
            module_id=module_id,
            canonical_name=canonical_name,
        )

    async def update_profile(
        self,
        user: UserDTO,
        name: Optional[str] = None,
        city_id: Optional[int] = None,
        direction_id: Optional[int] = None,
        direction_name: Optional[str] = None,
        unique_skill_ids: Optional[list[int]] = None,
        skill_name_list: Optional[list[str]] = None,
        timezone: Optional[str] = None,
        hashed_password: Optional[str] = None,
    ) -> UserDTO:
        direction_changed = direction_id is not None and direction_id != user.direction_id

        if unique_skill_ids is not None and skill_name_list is None:
            skill_name_list = []
            for skill_id in unique_skill_ids:
                skill = await self._skill_repository.get_by_id(skill_id)
                if not skill:
                    raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=f"Skill {skill_id} not found")
                if skill.name:
                    skill_name_list.append(skill.name)

        existing_base_ids: set[int] = set()
        if direction_changed or unique_skill_ids is not None:
            base_res = await self._user_skill_repository.get_by_user_id(
                user_id=user.id,
                to_learn=False,
            )
            existing_base_ids = {
                us.skill_id for us in base_res.items if us.skill_id is not None
            }

        if unique_skill_ids is None and direction_changed:
            unique_skill_ids = list(existing_base_ids)
            skill_name_list = []
            for skill_id in unique_skill_ids:
                skill = await self._skill_repository.get_by_id(skill_id)
                if not skill:
                    raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=f"Skill {skill_id} not found")
                if skill.name:
                    skill_name_list.append(skill.name)

        effective_direction = None
        if direction_id is not None:
            if direction_name:
                effective_direction = DirectionDTO(
                    id=direction_id,
                    name=direction_name,
                )
            else:
                effective_direction = await self._direction_repository.get_by_id(direction_id)
            if not effective_direction:
                raise HTTPException(
                    status_code=s.HTTP_404_NOT_FOUND,
                    detail=f"Direction {direction_id} not found",
                )
        elif (direction_changed or unique_skill_ids is not None) and user.direction_id is not None:
            effective_direction = await self._direction_repository.get_by_id(user.direction_id)
            if not effective_direction:
                raise HTTPException(
                    status_code=s.HTTP_404_NOT_FOUND,
                    detail=f"Direction {user.direction_id} not found",
                )

        removed_base_ids: set[int] = set()
        added_base_ids: set[int] = set()
        removed_to_module: List[UserSkillDTO] = []
        if unique_skill_ids is not None:
            new_ids_set = set(unique_skill_ids)
            removed_base_ids = existing_base_ids - new_ids_set
            added_base_ids = new_ids_set - existing_base_ids

            if removed_base_ids and effective_direction is not None:
                for skill_id in removed_base_ids:
                    skill = await self._skill_repository.get_by_id(skill_id)
                    if not skill or not skill.name:
                        continue

                    ai_check = await self._openai_service.check_skill_in_direction(
                        direction_name=effective_direction.name or "",
                        skill_name=skill.name,
                        model=ChatGPTModel.GPT_4_1,
                    )

                    if ai_check.get("belongs") is True:
                        removed_to_module.append(
                            UserSkillDTO(
                                skill=SkillDTO(name=skill.name),
                                to_learn=True,
                                match_percentage=ai_check.get("match_percentage"),
                            )
                        )

        ai_skills: List[UserSkillDTO] = []
        if direction_changed:
            if effective_direction is None:
                raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="Direction not found")
            ai_skills = await self.get_theoretical_skills(
                direction_name=effective_direction.name or "",
                skill_names=skill_name_list or [],
            )
            if removed_to_module:
                ai_skills = ai_skills + removed_to_module
        elif removed_to_module:
            ai_skills = removed_to_module

        effective_city_id = city_id if city_id is not None else user.city_id
        effective_direction_id = direction_id if direction_id is not None else user.direction_id

        async with self._uow:
            user_update = UserDTO(
                name=name,
                city_id=city_id,
                direction_id=direction_id,
                password=hashed_password,
                timezone=timezone,
            )
            updated = await self._user_repository.update(user_id=user.id, dto=user_update)
            if updated is None:
                raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="User not found")

            if direction_changed:
                await self._user_skill_repository.delete_by_user_and_to_learn(
                    user_id=user.id,
                    to_learn=True,
                )
                await self._user_question_repository.delete_by_user(user_id=user.id)
                await self._interview_question_repository.delete_by_user(user_id=user.id)
                await self._interview_session_repository.delete_by_user(user_id=user.id)

            if unique_skill_ids is not None:
                for skill_id in removed_base_ids:
                    await self._user_skill_repository.delete(user_id=user.id, skill_id=skill_id)

                for skill_id in added_base_ids:
                    existing = await self._user_skill_repository.get_by_user_and_skill(
                        user_id=user.id,
                        skill_id=skill_id,
                    )
                    if existing and existing.to_learn:
                        await self._user_skill_repository.update(
                            user_id=user.id,
                            skill_id=skill_id,
                            dto=UserSkillDTO(to_learn=False, match_percentage=None),
                        )
                        await self._user_question_repository.delete_by_user_and_module(
                            user_id=user.id,
                            module_id=skill_id,
                        )
                    elif existing is None:
                        await self._user_skill_repository.add(
                            UserSkillDTO(
                                user_id=user.id,
                                skill_id=skill_id,
                                to_learn=False,
                            )
                        )

            if ai_skills and effective_direction is not None:
                attach_skill_names = skill_name_list or []
                attach_skill_ids = unique_skill_ids or list(existing_base_ids)
                await self.attach_ai_skills_as_modules(
                    user_id=user.id,
                    ai_skills=ai_skills,
                    existing_skill_names=attach_skill_names,
                    existing_skill_ids=attach_skill_ids,
                )

            if effective_city_id is not None and effective_direction_id is not None:
                existing_salary = await self._salary_repository.get_by_city_and_direction(
                    city_id=effective_city_id,
                    direction_id=effective_direction_id,
                )

                if existing_salary is None:
                    city = await self._city_repository.get_by_id(
                        effective_city_id,
                        populate_country=True,
                    )
                    if not city:
                        raise HTTPException(
                            status_code=s.HTTP_404_NOT_FOUND,
                            detail=f"City {effective_city_id} not found",
                        )

                    if effective_direction is None:
                        effective_direction = await self._direction_repository.get_by_id(
                            effective_direction_id,
                        )
                        if not effective_direction:
                            raise HTTPException(
                                status_code=s.HTTP_404_NOT_FOUND,
                                detail=f"Direction {effective_direction_id} not found",
                            )

                    if not city.country or not city.country.name:
                        raise HTTPException(
                            status_code=s.HTTP_404_NOT_FOUND,
                            detail="City country not found",
                        )

                    ai_salary = await self._openai_service.get_direction_salary(
                        country=city.country.name,
                        city=city.name or "",
                        direction=effective_direction.name or "",
                        model=ChatGPTModel.GPT_4_1,
                    )
                    if not ai_salary:
                        raise HTTPException(
                            status_code=s.HTTP_408_REQUEST_TIMEOUT,
                            detail="Failed to generate salary, please try again",
                        )

                    await self._salary_repository.add(
                        SalaryDTO(
                            city_id=effective_city_id,
                            direction_id=effective_direction_id,
                            amount=ai_salary["amount"],
                            currency=ai_salary["currency"],
                        )
                    )

        return updated

    async def _update_user_profile(
        self,
        user_id: int,
        name: str,
        city_id: int,
        direction_id: int,
        timezone: str,
    ) -> Optional[UserDTO]:
        user_update = UserDTO(
            name=name,
            city_id=city_id,
            direction_id=direction_id,
            is_onboarding_completed=True,
            timezone=timezone,
        )
        return await self._user_repository.update(user_id=user_id, dto=user_update)

    async def _create_salary_if_needed(
        self,
        city_id: int,
        direction_id: int,
        salary_context: Dict[str, str],
    ) -> None:
        ai_salary = await self._openai_service.get_direction_salary(
            country=salary_context["country"],
            city=salary_context["city"],
            direction=salary_context["direction"],
            model=ChatGPTModel.GPT_4_1,
        )
        if not ai_salary:
            raise HTTPException(
                status_code=s.HTTP_408_REQUEST_TIMEOUT,
                detail="Failed to generate salary, please try again",
            )

        await self._salary_repository.add(
            SalaryDTO(
                city_id=city_id,
                direction_id=direction_id,
                amount=ai_salary["amount"],
                currency=ai_salary["currency"],
            )
        )

    async def _attach_selected_skills(
        self,
        user_id: int,
        unique_skill_ids: List[int],
    ) -> List[UserSkillDTO]:
        skills_list: List[UserSkillDTO] = []
        for skill_id in unique_skill_ids:
            await self._user_skill_repository.add(
                UserSkillDTO(
                    user_id=user_id,
                    skill_id=skill_id,
                )
            )
            skills_list.append(
                UserSkillDTO(
                    user_id=user_id,
                    skill_id=skill_id,
                    to_learn=False,
                )
            )
        return skills_list

    async def _attach_ai_skills_as_modules(
        self,
        user_id: int,
        ai_skills: List[UserSkillDTO],
        existing_skill_names: List[str],
        existing_skill_ids: List[int],
    ) -> List[UserSkillDTO]:
        modules_list: List[UserSkillDTO] = []

        added_skill_ids = set(existing_skill_ids)
        added_skill_names = {name.strip().lower() for name in existing_skill_names}

        for ai_skill in ai_skills:
            if not ai_skill.skill or not ai_skill.skill.name:
                continue

            skill_name = ai_skill.skill.name.strip()
            if not skill_name:
                continue

            if skill_name.lower() in added_skill_names:
                continue

            skill_id, canonical_name = await self._get_or_create_skill(skill_name=skill_name)

            if not skill_id or skill_id in added_skill_ids:
                continue

            await self._user_skill_repository.add(
                UserSkillDTO(
                    user_id=user_id,
                    skill_id=skill_id,
                    to_learn=True,
                    match_percentage=ai_skill.match_percentage,
                )
            )
            modules_list.append(
                UserSkillDTO(
                    user_id=user_id,
                    skill_id=skill_id,
                    to_learn=True,
                    match_percentage=ai_skill.match_percentage,
                )
            )

            added_skill_ids.add(skill_id)
            added_skill_names.add(skill_name.lower())

            await self._seed_questions_if_needed(
                module_id=skill_id,
                canonical_name=canonical_name,
            )

        return modules_list

    async def _get_or_create_skill(self, skill_name: str) -> tuple[Optional[int], str]:
        existing_skill = await self._skill_repository.get_by_name(skill_name)
        if existing_skill and existing_skill.name and existing_skill.name.lower() == skill_name.lower():
            return existing_skill.id, existing_skill.name

        created_skill = await self._skill_repository.add(SkillDTO(name=skill_name))
        if not created_skill:
            return None, skill_name
        return created_skill.id, created_skill.name

    async def _seed_questions_if_needed(self, module_id: int, canonical_name: str) -> None:
        existing_questions = await self._question_repository.get(
            pagination=PaginationDTO[QuestionDTO](per_page=1),
            module_id=module_id,
        )
        if existing_questions.total != 0:
            return

        ai_questions = await self._openai_service.get_skill_theoretical_questions(
            skill_name=canonical_name,
            model=ChatGPTModel.GPT_4_1,
        )
        for q in ai_questions:
            q.skill_id = module_id
            await self._question_repository.add(q)
