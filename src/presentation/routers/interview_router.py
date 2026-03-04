from typing import Annotated

from fastapi import APIRouter, status as s, Depends

from src.application.interview.interfaces import IInterviewController
from src.application.users.dtos import UserDTO
from src.domain.responses import RESPONSE_400, RESPONSE_401
from src.presentation.depends.controllers import get_interview_controller
from src.presentation.depends.security import get_access_user

router = APIRouter(
    prefix="/interviews",
    tags=["interview"],
)

@router.post(
    "/start",
    status_code=s.HTTP_201_CREATED,
    responses={
        s.HTTP_400_BAD_REQUEST: RESPONSE_400,
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401,
    },
)
async def start_interview(
    controller: Annotated[IInterviewController, Depends(get_interview_controller)],
    user: UserDTO = Depends(get_access_user),
):
    return await controller.start(user_id=user.id)
