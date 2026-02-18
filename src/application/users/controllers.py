from typing import Dict

from fastapi import HTTPException, status as s

from src.application.users.dtos import UserDTO
from src.application.users.interfaces import IUserController, IUserRepository, IEmailOtpService
from src.domain.interfaces import IUoW, IHashService, IJWTService


class UserController(IUserController):
    def __init__(
            self,
            uow: IUoW,
            user_repository: IUserRepository,
            email_otp_service: IEmailOtpService,
            hash_service: IHashService,
            jwt_service: IJWTService,
    ):
        self._uow = uow
        self._user_repository = user_repository
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

        async with self._uow as uow:
            created = await self._user_repository.add(
                user_data.to_payload(exclude_none=True)
            )

        payload = {
            "user_id": created.id,
        }

        access_token = self._jwt_service.encode_token(data=payload)
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
        }

        access_token = self._jwt_service.encode_token(data=payload)
        refresh_token = self._jwt_service.encode_token(data=payload, is_access_token=False)

        return {
            "detail": "Logged in successfully",
            "access_token": access_token,
            "refresh_token": refresh_token,
        }