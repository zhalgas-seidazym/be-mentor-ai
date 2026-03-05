from typing import Annotated

from fastapi import APIRouter, status as s, Depends, Query

from src.application.users.dtos import UserDTO
from src.application.users.user.interfaces import IUserController
from src.domain.responses import *
from src.presentation.depends.controllers import get_user_controller
from src.presentation.depends.security import get_access_user
from src.presentation.schemas.users_schema import UserProfileCreateSchema, UserProfileUpdateSchema

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.post(
    '/profile',
    summary="Create user profile",
    status_code=s.HTTP_201_CREATED,
    response_model=UserDTO,
    response_model_exclude={"password"},
    responses={
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401,
        s.HTTP_404_NOT_FOUND: RESPONSE_404,
        s.HTTP_409_CONFLICT: RESPONSE_409
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
        timezone=body.timezone,
    )

@router.get(
    '/profile',
    summary="Get current user profile",
    status_code=s.HTTP_200_OK,
    response_model=UserDTO,
    response_model_exclude={"password"},
    responses={
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401,
        s.HTTP_404_NOT_FOUND: RESPONSE_404,
    }
)
async def get_profile(
        controller: Annotated[IUserController, Depends(get_user_controller)],
        user: UserDTO = Depends(get_access_user),
        populate_city: bool = Query(False),
        populate_direction: bool = Query(False),
        populate_skills: bool = Query(False),
):
    return await controller.get_profile(
        user_id=user.id,
        populate_city=populate_city,
        populate_direction=populate_direction,
        populate_skills=populate_skills,
    )

@router.get(
    '/profile/streak',
    summary="Get user interview streak",
    status_code=s.HTTP_200_OK,
    responses={
        s.HTTP_200_OK: {
            "description": "User streak",
            "content": {
                "application/json": {
                    "example": {
                        "current_streak": 5,
                        "longest_streak": 12,
                        "last_interview_day": "2026-03-05",
                        "timezone": "Asia/Almaty",
                    }
                }
            }
        },
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401,
        s.HTTP_404_NOT_FOUND: RESPONSE_404,
    }
)
async def get_profile_streak(
        controller: Annotated[IUserController, Depends(get_user_controller)],
        user: UserDTO = Depends(get_access_user),
):
    return await controller.get_profile_streak(user_id=user.id)

@router.patch(
    '/profile',
    summary="Update user profile",
    status_code=s.HTTP_200_OK,
    response_model=UserDTO,
    response_model_exclude={"password"},
    responses={
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401,
        s.HTTP_404_NOT_FOUND: RESPONSE_404,
        s.HTTP_400_BAD_REQUEST: RESPONSE_400,
        s.HTTP_408_REQUEST_TIMEOUT: RESPONSE_408,
    }
)
async def update_profile(
        body: UserProfileUpdateSchema,
        controller: Annotated[IUserController, Depends(get_user_controller)],
        user: UserDTO = Depends(get_access_user),
):
    return await controller.update_profile(
        user_id=user.id,
        name=body.name,
        city_id=body.city_id,
        password=body.password,
        new_password=body.new_password,
    )

@router.delete(
    '',
    summary="Delete current user",
    status_code=s.HTTP_200_OK,
    responses={
        s.HTTP_200_OK: {
            "description": "User deleted",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User deleted successfully"
                    }
                }
            }
        },
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401,
        s.HTTP_404_NOT_FOUND: RESPONSE_404,
    }
)
async def delete_user(
        controller: Annotated[IUserController, Depends(get_user_controller)],
        user: UserDTO = Depends(get_access_user),
):
    return await controller.delete_user(user_id=user.id)
