from typing import Annotated

from fastapi import APIRouter, status as s, Depends, Body
from pydantic import EmailStr

from src.application.users.dtos import UserDTO
from src.application.users.interfaces import IUserController
from src.domain.responses import RESPONSE_404
from src.presentation.depends.controllers import get_user_controller
from src.presentation.schemas.user_schemas import UserRegisterSchema

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