from typing import Dict, Optional

from fastapi import HTTPException, status as s

from src.application.users.dtos import UserDTO
from src.application.directions.interfaces import IDirectionRepository, ISalaryRepository
from src.application.locations.interfaces import ICityRepository
from src.application.skills.dtos import SkillDTO, UserSkillDTO
from src.application.skills.interfaces import ISkillRepository, IUserSkillRepository
from src.application.questions.dtos import QuestionDTO
from src.application.questions.interfaces import IQuestionRepository
from src.application.directions.dtos import SalaryDTO
from src.application.users.interfaces import IUserRepository
from src.application.users.user.interfaces import IUserController
from src.application.users.auth.interfaces import IHashService
from src.domain.interfaces import IUoW, IOpenAIService
from src.domain.base_dto import PaginationDTO
from src.domain.value_objects import ChatGPTModel


class UserController(IUserController):
    def __init__(
            self,
            uow: IUoW,
            user_repository: IUserRepository,
            user_skill_repository: IUserSkillRepository,
            skill_repository: ISkillRepository,
            question_repository: IQuestionRepository,
            direction_repository: IDirectionRepository,
            salary_repository: ISalaryRepository,
            city_repository: ICityRepository,
            openai_service: IOpenAIService,
            hash_service: IHashService,
    ):
        self._uow = uow
        self._user_repository = user_repository
        self._user_skill_repository = user_skill_repository
        self._skill_repository = skill_repository
        self._question_repository = question_repository
        self._direction_repository = direction_repository
        self._salary_repository = salary_repository
        self._city_repository = city_repository
        self._openai_service = openai_service
        self._hash_service = hash_service

    async def create_profile(
        self,
        user_id: int,
        name: str,
        city_id: int,
        direction_id: int,
        skill_ids: list[int],
        timezone: str,
    ) -> UserDTO:
        # Check that user exists and not yet onboarded
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="User not found")

        if user.is_onboarding_completed:
            raise HTTPException(status_code=s.HTTP_409_CONFLICT, detail="User already onboarding")

        # Validate city and direction references
        city = await self._city_repository.get_by_id(city_id, populate_country=True)
        if not city:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=f"City {city_id} not found")

        direction = await self._direction_repository.get_by_id(direction_id)
        if not direction:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=f"Direction {direction_id} not found")

        existing_salary = await self._salary_repository.get_by_city_and_direction(
            city_id=city_id,
            direction_id=direction_id,
        )

        # Load selected skills and prepare list for AI
        skill_name_list = []
        unique_skill_ids = list(dict.fromkeys(skill_ids))
        for skill_id in unique_skill_ids:
            skill = await self._skill_repository.get_by_id(skill_id)
            if not skill:
                raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=f"Skill {skill_id} not found")
            if skill.name:
                skill_name_list.append(skill.name)

        # Ask AI for additional theoretical skills
        ai_skills = await self._openai_service.get_direction_theoretical_skills(
            direction_name=direction.name or "",
            skills=skill_name_list,
            model=ChatGPTModel.GPT_4_1,
        )

        skills_list = []
        modules_list = []

        async with self._uow:
            # Update user profile fields in DB
            user_update = UserDTO(
                name=name,
                city_id=city_id,
                direction_id=direction_id,
                is_onboarding_completed=True,
                timezone=timezone,
            )
            user = await self._user_repository.update(user_id=user_id, dto=user_update)
            if user is None:
                raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="User not found")

            # Ensure salary exists for user's city and direction
            if existing_salary is None:
                if not city.country or not city.country.name:
                    raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="City country not found")

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

                await self._salary_repository.add(
                    SalaryDTO(
                        city_id=city_id,
                        direction_id=direction_id,
                        amount=ai_salary["amount"],
                        currency=ai_salary["currency"],
                    )
                )

            # Attach selected skills to the user
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

            # Attach AI skills as modules (to_learn)
            added_skill_ids = set(unique_skill_ids)
            added_skill_names = {name.strip().lower() for name in skill_name_list}

            for ai_skill in ai_skills:
                # Skip invalid AI entries
                if not ai_skill.skill or not ai_skill.skill.name:
                    continue

                skill_name = ai_skill.skill.name.strip()
                if not skill_name:
                    continue

                # Avoid duplicates by name
                if skill_name.lower() in added_skill_names:
                    continue

                # Find or create skill record
                existing_skill = await self._skill_repository.get_by_name(skill_name)
                if existing_skill and existing_skill.name and existing_skill.name.lower() == skill_name.lower():
                    skill_id = existing_skill.id
                    canonical_name = existing_skill.name
                else:
                    created_skill = await self._skill_repository.add(
                        SkillDTO(name=skill_name)
                    )
                    skill_id = created_skill.id if created_skill else None
                    canonical_name = created_skill.name if created_skill else skill_name

                # Skip if skill wasn't created or already attached
                if not skill_id or skill_id in added_skill_ids:
                    continue

                # Link AI skill to user as module
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

                # Track added skill names/ids
                added_skill_ids.add(skill_id)
                added_skill_names.add(skill_name.lower())

                # Seed questions for new skill if none exist
                existing_questions = await self._question_repository.get(
                    pagination=PaginationDTO[QuestionDTO](per_page=1),
                    skill_id=skill_id,
                )
                if existing_questions.total == 0:
                    ai_questions = await self._openai_service.get_skill_theoretical_questions(
                        skill_name=canonical_name,
                        model=ChatGPTModel.GPT_4_1,
                    )
                    for q in ai_questions:
                        q.skill_id = skill_id
                        await self._question_repository.add(q)

        # Prepare response DTO without extra DB roundtrip
        user.name = name
        user.city_id = city_id
        user.direction_id = direction_id
        user.is_onboarding_completed = True
        user.skills = skills_list
        user.modules = modules_list
        return user

    async def get_profile(
        self,
        user_id: int,
        populate_city: bool = False,
        populate_direction: bool = False,
        populate_skills: bool = False,
    ) -> UserDTO:
        user = await self._user_repository.get_by_id(
            user_id=user_id,
            populate_city=populate_city,
            populate_skills=populate_skills,
            populate_direction=populate_direction,
        )

        if not user:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="User not found")

        return user

    async def get_profile_streak(self, user_id: int) -> Dict[str, Optional[object]]:
        user = await self._user_repository.get_by_id(user_id=user_id)
        if not user:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="User not found")

        return {
            "current_streak": user.current_streak,
            "longest_streak": user.longest_streak,
            "last_interview_day": user.last_interview_day,
            "timezone": user.timezone,
        }

    async def update_profile(
        self,
        user_id: int,
        name: Optional[str] = None,
        city_id: Optional[int] = None,
        password: Optional[str] = None,
        new_password: Optional[str] = None,
    ) -> UserDTO:
        user = await self._user_repository.get_by_id(user_id=user_id)
        if not user:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="User not found")

        # Password update requires both old and new password.
        if (password is None) != (new_password is None):
            raise HTTPException(
                status_code=s.HTTP_400_BAD_REQUEST,
                detail="Both password and new_password are required to change password",
            )

        hashed_password = None
        if password is not None and new_password is not None:
            if not self._hash_service.verify_password(password, user.password):
                raise HTTPException(status_code=s.HTTP_400_BAD_REQUEST, detail="Incorrect password")
            hashed_password = self._hash_service.hash_password(new_password)

        city = None
        if city_id is not None:
            city = await self._city_repository.get_by_id(city_id, populate_country=True)
            if not city:
                raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=f"City {city_id} not found")

        existing_salary = None
        direction = None
        ai_salary = None

        if city is not None and user.direction_id is not None:
            existing_salary = await self._salary_repository.get_by_city_and_direction(
                city_id=city_id,
                direction_id=user.direction_id,
            )

            if existing_salary is None:
                direction = await self._direction_repository.get_by_id(user.direction_id)
                if not direction:
                    raise HTTPException(
                        status_code=s.HTTP_404_NOT_FOUND,
                        detail=f"Direction {user.direction_id} not found",
                    )

                if not city.country or not city.country.name:
                    raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="City country not found")

                ai_salary = await self._openai_service.get_direction_salary(
                    country=city.country.name,
                    city=city.name or "",
                    direction=direction.name or "",
                    model=ChatGPTModel.GPT_4_1,
                )
                if not ai_salary:
                    raise HTTPException(
                        status_code=s.HTTP_408_REQUEST_TIMEOUT,
                        detail="Failed to generate salary, please try again",
                    )

        async with self._uow:
            user_update = UserDTO(
                name=name,
                city_id=city_id,
                password=hashed_password,
            )
            updated = await self._user_repository.update(user_id=user_id, dto=user_update)
            if updated is None:
                raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="User not found")

            if ai_salary and city_id is not None and user.direction_id is not None:
                await self._salary_repository.add(
                    SalaryDTO(
                        city_id=city_id,
                        direction_id=user.direction_id,
                        amount=ai_salary["amount"],
                        currency=ai_salary["currency"],
                    )
                )

        return updated

    async def delete_user(self, user_id: int) -> Dict:
        async with self._uow:
            deleted = await self._user_repository.delete(user_id=user_id)

        if not deleted:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="User not found")

        return {
            "detail": "User deleted successfully",
        }
