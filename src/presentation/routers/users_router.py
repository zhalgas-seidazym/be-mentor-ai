from typing import Annotated

from fastapi import APIRouter, status as s, Depends, Body
from pydantic import EmailStr

from src.application.users.dtos import UserDTO
from src.application.users.interfaces import IUserController
from src.domain.base_schema import PasswordSchema
from src.domain.responses import *
from src.presentation.depends.controllers import get_user_controller
from src.presentation.depends.security import get_reset_user, get_refresh_user, get_access_user
from src.presentation.schemas.users_schema import UserRegisterSchema, UserProfileCreateSchema

router = APIRouter(
    prefix="/user",
    tags=["user"]
)

@router.post(
    "/send-otp",
    status_code=s.HTTP_200_OK,
    responses={
        s.HTTP_200_OK: {
            "description": "OTP code sent",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "OTP code sent successfully"
                    }
                }
            }
        },
        s.HTTP_400_BAD_REQUEST: {
            "description": "OTP was already sent and has not expired yet",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "OTP was already sent and has not expired yet"
                    }
                }
            }
        }
    }
)
async def send_otp(
        controller: Annotated[IUserController, Depends(get_user_controller)],
        email: EmailStr = Body(),
):
    return await controller.send_otp(email.__str__())

@router.post(
    "/verify-otp/register",
    status_code=s.HTTP_201_CREATED,
    responses={
        s.HTTP_201_CREATED: {
            "description": "User created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User created successfully",
                        "user_id": 1,
                        "access_token": "token",
                        "refresh_token": "token",
                    }
                }
            }
        },
        s.HTTP_400_BAD_REQUEST: {
            "description": "Incorrect or expired otp code, or incorrect credentials",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Incorrect or expired otp code, or incorrect credentials"
                    }
                }
            }
        },
        s.HTTP_409_CONFLICT: {
            "description": "User already exists",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User already exists"
                    }
                }
            }
        }
    }
)
async def verify_otp_and_register(
        body: UserRegisterSchema,
        controller: Annotated[IUserController, Depends(get_user_controller)],
):
    return await controller.verify_otp_and_register(
        user_data=UserDTO(**{k: v for k, v in body.dict().items() if k != "code"}), code=body.code
    )

@router.post(
    '/login',
    status_code=s.HTTP_200_OK,
    responses={
        s.HTTP_200_OK: {
            "description": "Logged in successfully",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Logged in successfully",
                        "access_token": "token",
                        "refresh_token": "token",
                    }
                }
            }
        },
        s.HTTP_404_NOT_FOUND: RESPONSE_404,
        s.HTTP_400_BAD_REQUEST: {
            "description": "Incorrect credentials",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Incorrect credentials"
                    }
                }
            }
        }
    }
)
async def login(
        controller: Annotated[IUserController, Depends(get_user_controller)],
        email: EmailStr = Body(),
        password: str = Body(),
):
    return await controller.login(user_data=UserDTO(email=email.__str__(), password=password))

@router.post(
    '/verify-otp/password-reset-token',
    status_code=s.HTTP_200_OK,
    responses={
        s.HTTP_200_OK: {
            "description": "Token for reset password",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Otp verified successfully",
                        "password_reset_token": "token",
                    }
                }
            }
        },
        s.HTTP_400_BAD_REQUEST: RESPONSE_400,
        s.HTTP_404_NOT_FOUND: RESPONSE_404,
    }
)
async def verify_otp_password_reset(
        controller: Annotated[IUserController, Depends(get_user_controller)],
        email: EmailStr = Body(),
        code: str = Body(),
):
    return await controller.verify_otp_and_password_token(UserDTO(email=email.__str__()), code=code)

@router.post(
    '/reset-password',
    status_code=s.HTTP_200_OK,
    responses={
        s.HTTP_200_OK: {
            "description": "Reset password successfully",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Reset password successfully",
                    }
                }
            }
        },
        s.HTTP_400_BAD_REQUEST: RESPONSE_400,
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401
    }
)
async def reset_password(
        controller: Annotated[IUserController, Depends(get_user_controller)],
        password: PasswordSchema,
        user: UserDTO = Depends(get_reset_user)
):
    user.password = password.dict().get("password")
    return await controller.reset_password(user_data=user)

@router.post(
    '/refresh-token',
    status_code=s.HTTP_200_OK,
    responses={
        s.HTTP_200_OK: {
            "description": "Refreshed token successfully",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Refreshed token successfully",
                        "access_token": "token",
                        "refresh_token": "token"
                    }
                }
            }
        },
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401,
    }
)
async def refresh_token(
        controller: Annotated[IUserController, Depends(get_user_controller)],
        user: UserDTO = Depends(get_refresh_user)
):
    return await controller.refresh_token(user)

@router.post(
    '/profile',
    status_code=s.HTTP_201_CREATED,
    response_model=UserDTO,
    response_model_exclude={"password"},
    responses={
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401,
        s.HTTP_404_NOT_FOUND: RESPONSE_404,
    }
)
async def create_profile(
        body: UserProfileCreateSchema,
        controller: Annotated[IUserController, Depends(get_user_controller)],
        user: UserDTO = Depends(get_access_user),
):
    return await controller.create_profile(
        user_id=user.id,
        name=body.name,
        city_id=body.city_id,
        direction_id=body.direction_id,
        skill_ids=body.skill_ids,
    )
