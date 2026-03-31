from typing import Dict

from fastapi import HTTPException, status as s

from src.application.users.dtos import UserDTO
from src.application.users.interfaces import IUserRepository
from src.application.users.auth.interfaces import (
    IAuthController,
    IEmailOtpService,
    IHashService,
    IOAuthService,
)
from src.domain.interfaces import IUoW, IJWTService
from src.domain.value_objects import TokenType
from src.infrastructure.integrations.airflow_client import AirflowClient


class AuthController(IAuthController):
    def __init__(
            self,
            uow: IUoW,
            user_repository: IUserRepository,
            email_otp_service: IEmailOtpService,
            hash_service: IHashService,
            oauth_service: IOAuthService,
            jwt_service: IJWTService,
            airflow_client: AirflowClient,
    ):
        self._uow = uow
        self._user_repository = user_repository
        self._email_otp_service = email_otp_service
        self._hash_service = hash_service
        self._oauth_service = oauth_service
        self._jwt_service = jwt_service
        self._airflow_client = airflow_client

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

        try:
            await self._airflow_client.trigger_dag(
                dag_id="vacancy_pipeline_orchestrator_dag",
                conf={"user_id": created.id},
            )
        except Exception:
            # Best-effort: do not block registration if Airflow is down.
            pass

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

        if user.password is None or len(user.password) == 0:
            raise HTTPException(status_code=s.HTTP_403_FORBIDDEN, detail=f"User has no password, login through OAuth or reset password")

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

    async def oauth_start(self, provider: str) -> Dict:
        return await self._oauth_service.build_authorization_url(provider=provider)

    async def oauth_callback(self, provider: str, code: str, state: str) -> Dict:
        oauth_data = await self._oauth_service.exchange_code_for_email(
            provider=provider,
            code=code,
            state=state,
        )

        user = await self._user_repository.get_by_email(oauth_data["email"])

        if user is None:
            async with self._uow:
                user = await self._user_repository.add(
                    UserDTO(
                        email=oauth_data["email"],
                        password=None,
                    )
                )

        payload = {
            "user_id": user.id,
            "type": TokenType.ACCESS.value,
        }
        access_token = self._jwt_service.encode_token(data=payload)
        payload["type"] = TokenType.REFRESH.value
        refresh_token = self._jwt_service.encode_token(data=payload, is_access_token=False)

        return {
            "detail": "OAuth authenticated successfully",
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
