from typing import Annotated, Literal
from urllib.parse import urlencode

from fastapi.responses import RedirectResponse
from fastapi import APIRouter, status as s, Depends, Body, Query
from pydantic import EmailStr

from app.settings import Settings
from src.application.users.dtos import UserDTO
from src.application.users.auth.interfaces import IAuthController
from src.domain.base_schema import PasswordSchema
from src.domain.responses import *
from src.presentation.depends.controllers import get_auth_controller
from src.presentation.depends.security import get_reset_user, get_refresh_user
from src.presentation.schemas.users_schema import UserRegisterSchema

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)
settings = Settings()


@router.post(
    "/send-otp",
    summary="Send OTP to email",
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
        controller: Annotated[IAuthController, Depends(get_auth_controller)],
        email: EmailStr = Body(),
):
    return await controller.send_otp(email.__str__())


@router.post(
    "/verify-otp/register",
    summary="Verify OTP and register",
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
        controller: Annotated[IAuthController, Depends(get_auth_controller)],
):
    return await controller.verify_otp_and_register(
        user_data=UserDTO(**{k: v for k, v in body.dict().items() if k != "code"}), code=body.code
    )


@router.post(
    '/login',
    summary="Login with credentials",
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
        },
        s.HTTP_403_FORBIDDEN: RESPONSE_403,
    }
)
async def login(
        controller: Annotated[IAuthController, Depends(get_auth_controller)],
        email: EmailStr = Body(),
        password: str = Body(),
):
    return await controller.login(user_data=UserDTO(email=email.__str__(), password=password))


@router.post(
    '/verify-otp/password-reset-token',
    summary="Verify OTP and issue reset token",
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
        controller: Annotated[IAuthController, Depends(get_auth_controller)],
        email: EmailStr = Body(),
        code: str = Body(),
):
    return await controller.verify_otp_and_password_token(UserDTO(email=email.__str__()), code=code)


@router.post(
    '/reset-password',
    summary="Reset password using reset token",
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
        controller: Annotated[IAuthController, Depends(get_auth_controller)],
        password: PasswordSchema,
        user: UserDTO = Depends(get_reset_user)
):
    user.password = password.dict().get("password")
    return await controller.reset_password(user_data=user)


@router.post(
    '/refresh-token',
    summary="Refresh access token",
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
        controller: Annotated[IAuthController, Depends(get_auth_controller)],
        user: UserDTO = Depends(get_refresh_user)
):
    return await controller.refresh_token(user)


@router.get(
    "/oauth/{provider}/start",
    summary="Start OAuth authorization",
    status_code=s.HTTP_200_OK,
    responses={
        s.HTTP_200_OK: {
            "description": "OAuth authorization URL created",
            "content": {
                "application/json": {
                    "example": {
                        "provider": "google",
                        "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
                        "state": "state_token",
                    }
                }
            },
        },
        s.HTTP_400_BAD_REQUEST: RESPONSE_400,
        s.HTTP_500_INTERNAL_SERVER_ERROR: RESPONSE_500,
    },
)
async def oauth_start(
        provider: Literal["google"],
        controller: Annotated[IAuthController, Depends(get_auth_controller)],
):
    return await controller.oauth_start(provider=provider)


@router.get(
    "/oauth/{provider}/callback",
    summary="OAuth callback",
    responses={
        s.HTTP_200_OK: {
            "description": "OAuth callback result (in url encode of redirect response)",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "OAuth authenticated successfully",
                        "access_token": "token",
                        "refresh_token": "token",
                    }
                }
            },
        },
        s.HTTP_302_FOUND: {
            "description": "Redirect to deep link with OAuth tokens",
            "headers": {
                "Location": {
                    "description": "Deep link with query params: detail, access_token, refresh_token",
                }
            },
        },
        s.HTTP_400_BAD_REQUEST: RESPONSE_400,
    },
)
async def oauth_callback(
        provider: Literal["google"],
        controller: Annotated[IAuthController, Depends(get_auth_controller)],
        code: str = Query(...),
        state: str = Query(...),
):
    auth_result = await controller.oauth_callback(provider=provider, code=code, state=state)
    query = urlencode(
        {
            "detail": auth_result["detail"],
            "access_token": auth_result["access_token"],
            "refresh_token": auth_result["refresh_token"],
        }
    )
    separator = "&" if "?" in settings.GOOGLE_DEEP_LINK_URI else "?"
    return RedirectResponse(url=f"{settings.GOOGLE_DEEP_LINK_URI}{separator}{query}", status_code=s.HTTP_302_FOUND)
