from typing import Dict, Optional

from fastapi import HTTPException, status as s

from src.application.users.dtos import UserDTO
from src.application.directions.dtos import SalaryDTO
from src.application.directions.interfaces import IDirectionRepository, ISalaryRepository
from src.application.locations.interfaces import ICityRepository
from src.application.skills.interfaces import ISkillRepository
from src.application.users.interfaces import IUserRepository
from src.application.users.user.interfaces import IUserController, IUserService
from src.application.users.auth.interfaces import IHashService
from src.domain.interfaces import IUoW, IOpenAIService
from src.domain.value_objects import ChatGPTModel


class UserController(IUserController):
    def __init__(
            self,
            uow: IUoW,
            user_repository: IUserRepository,
            skill_repository: ISkillRepository,
            direction_repository: IDirectionRepository,
            salary_repository: ISalaryRepository,
            city_repository: ICityRepository,
            openai_service: IOpenAIService,
            hash_service: IHashService,
            user_service: IUserService,
    ):
        self._uow = uow
        self._user_repository = user_repository
        self._skill_repository = skill_repository
        self._direction_repository = direction_repository
        self._salary_repository = salary_repository
        self._city_repository = city_repository
        self._openai_service = openai_service
        self._hash_service = hash_service
        self._user_service = user_service

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
        ai_skills = await self._user_service.get_theoretical_skills(
            direction_name=direction.name or "",
            skill_names=skill_name_list,
        )

        existing_salary = await self._salary_repository.get_by_city_and_direction(
            city_id=city_id,
            direction_id=direction_id,
        )

        salary_context = None
        if existing_salary is None:
            if not city.country or not city.country.name:
                raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="City country not found")

            salary_context = {
                "country": city.country.name,
                "city": city.name or "",
                "direction": direction.name or "",
            }

        return await self._user_service.create_profile(
            user_id=user_id,
            name=name,
            city_id=city_id,
            direction_id=direction_id,
            timezone=timezone,
            unique_skill_ids=unique_skill_ids,
            skill_name_list=skill_name_list,
            ai_skills=ai_skills,
            salary_context=salary_context,
        )

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
