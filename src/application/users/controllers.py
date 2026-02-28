from typing import Dict

from fastapi import HTTPException, status as s

from src.application.users.dtos import UserDTO
from src.application.directions.interfaces import IDirectionRepository
from src.application.locations.interfaces import ICityRepository
from src.application.skills.dtos import SkillDTO
from src.application.skills.interfaces import ISkillRepository
from src.application.users.dtos import UserSkillDTO
from src.application.users.interfaces import (
    IUserController,
    IUserRepository,
    IEmailOtpService,
    IHashService,
    IUserSkillRepository,
)
from src.domain.interfaces import IUoW, IJWTService, IOpenAIService
from src.domain.value_objects import TokenType, ChatGPTModel


class UserController(IUserController):
    def __init__(
            self,
            uow: IUoW,
            user_repository: IUserRepository,
            user_skill_repository: IUserSkillRepository,
            skill_repository: ISkillRepository,
            direction_repository: IDirectionRepository,
            city_repository: ICityRepository,
            openai_service: IOpenAIService,
            email_otp_service: IEmailOtpService,
            hash_service: IHashService,
            jwt_service: IJWTService,
    ):
        self._uow = uow
        self._user_repository = user_repository
        self._user_skill_repository = user_skill_repository
        self._skill_repository = skill_repository
        self._direction_repository = direction_repository
        self._city_repository = city_repository
        self._openai_service = openai_service
        self._email_otp_service = email_otp_service
        self._hash_service = hash_service
        self._jwt_service = jwt_service

    async def send_otp(self, email: str) -> Dict:
        await self._email_otp_service.send_otp(email)
        return {
            "detail": "OTP code sent successfully",
        }

    async def verify_otp_and_register(self, user_data: UserDTO, code: str) -> Dict:
        user_check = await self._user_repository.get_by_email(user_data.email)
        if user_check:
            raise HTTPException(status_code=s.HTTP_409_CONFLICT,
                                detail=f"User with {user_data.email} already exists")

        await self._email_otp_service.verify_otp(user_data.email, code)

        user_data.password = self._hash_service.hash_password(user_data.password)

        async with self._uow:
            created = await self._user_repository.add(
                user_data
            )

        payload = {
            "user_id": created.id,
            'type': TokenType.ACCESS.value
        }
        access_token = self._jwt_service.encode_token(data=payload)
        payload['type'] = TokenType.REFRESH.value
        refresh_token = self._jwt_service.encode_token(data=payload, is_access_token=False)

        return {
            "detail": "OTP verified and user created successfully",
            "user_id": created.id,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    async def login(self, user_data: UserDTO) -> Dict:
        user = await self._user_repository.get_by_email(user_data.email)

        if user is None:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=f"User with {user_data.email} not found")

        password_check = self._hash_service.verify_password(user_data.password, user.password)

        if not password_check:
            raise HTTPException(status_code=s.HTTP_400_BAD_REQUEST, detail=f"Incorrect credentials")

        payload = {
            "user_id": user.id,
            'type': TokenType.ACCESS.value
        }
        access_token = self._jwt_service.encode_token(data=payload)
        payload['type'] = TokenType.REFRESH.value
        refresh_token = self._jwt_service.encode_token(data=payload, is_access_token=False)

        return {
            "detail": "Logged in successfully",
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    async def verify_otp_and_password_token(self, user_data: UserDTO, code: str) -> Dict:
        user = await self._user_repository.get_by_email(user_data.email)

        if not user:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=f"User with {user_data.email} not found")

        await self._email_otp_service.verify_otp(user_data.email, code)

        payload = {
            "user_id": user.id,
            'type': TokenType.PASSWORD_RESET.value
        }

        password_reset_token = self._jwt_service.encode_token(data=payload, expires_delta=5)

        return {
            "detail": "OTP verified successfully",
            "password_reset_token": password_reset_token
        }

    async def reset_password(self, user_data: UserDTO) -> Dict:
        user_data.password = self._hash_service.hash_password(user_data.password)

        async with self._uow:
            await self._user_repository.update(user_id=user_data.id, dto=user_data)

        return {
            "detail": "Password updated successfully",
        }

    async def refresh_token(self, user_data: UserDTO) -> Dict:
        payload = {
            "user_id": user_data.id,
            'type': TokenType.ACCESS.value
        }

        access_token = self._jwt_service.encode_token(data=payload)
        payload['type'] = TokenType.REFRESH.value
        refresh_token = self._jwt_service.encode_token(data=payload, is_access_token=False)


        return {
            "detail": "Refreshed token successfully",
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    async def create_profile(
        self,
        user_id: int,
        name: str,
        city_id: int,
        direction_id: int,
        skill_ids: list[int],
    ) -> UserDTO:
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="User not found")

        city = await self._city_repository.get_by_id(city_id)
        if not city:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=f"City {city_id} not found")

        direction = await self._direction_repository.get_by_id(direction_id)
        if not direction:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=f"Direction {direction_id} not found")

        skill_name_list = []
        unique_skill_ids = list(dict.fromkeys(skill_ids))
        for skill_id in unique_skill_ids:
            skill = await self._skill_repository.get_by_id(skill_id)
            if not skill:
                raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=f"Skill {skill_id} not found")
            if skill.name:
                skill_name_list.append(skill.name)

        ai_skills = await self._openai_service.get_direction_theoretical_skills(
            direction_name=direction.name or "",
            skills=skill_name_list,
            model=ChatGPTModel.GPT_4_1,
        )

        async with self._uow:
            user_update = UserDTO(
                name=name,
                city_id=city_id,
                direction_id=direction_id,
                is_onboarding_completed=True,
            )
            user = await self._user_repository.update(user_id=user_id, dto=user_update)

            for skill_id in unique_skill_ids:
                await self._user_skill_repository.add(
                    UserSkillDTO(
                        user_id=user_id,
                        skill_id=skill_id,
                    )
                )

            added_skill_ids = set(unique_skill_ids)
            added_skill_names = {name.strip().lower() for name in skill_name_list}

            for ai_skill in ai_skills:
                if not ai_skill.skill or not ai_skill.skill.name:
                    continue

                skill_name = ai_skill.skill.name.strip()
                if not skill_name:
                    continue

                if skill_name.lower() in added_skill_names:
                    continue

                existing_skill = await self._skill_repository.get_by_name(skill_name)
                if existing_skill and existing_skill.name and existing_skill.name.lower() == skill_name.lower():
                    skill_id = existing_skill.id
                else:
                    created_skill = await self._skill_repository.add(
                        SkillDTO(name=skill_name)
                    )
                    skill_id = created_skill.id if created_skill else None

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

                added_skill_ids.add(skill_id)
                added_skill_names.add(skill_name.lower())

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
