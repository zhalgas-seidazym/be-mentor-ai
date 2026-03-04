from typing import Annotated, Dict, Any

from fastapi import APIRouter, status as s, Depends, UploadFile, File, Form

from src.application.interview.interfaces import IInterviewController
from src.application.users.dtos import UserDTO
from src.domain.responses import RESPONSE_400, RESPONSE_401, RESPONSE_409
from src.presentation.depends.controllers import get_interview_controller
from src.presentation.depends.security import get_access_user

router = APIRouter(
    prefix="/interviews",
    tags=["interview"],
)

@router.post(
    "/start",
    status_code=s.HTTP_201_CREATED,
    response_model=Dict[str, Any],
    responses={
        s.HTTP_201_CREATED: {
            "description": "Interview started",
            "content": {
                "application/json": {
                    "example": {
                        "session_id": 12,
                        "main_question_index": 1,
                        "total_main_questions": 10,
                        "question": {
                            "interview_question_id": 501,
                            "question_id": 1001,
                            "text": "Explain the difference between stack and heap memory."
                        },
                        "followup_limit": 2
                    }
                }
            }
        },
        s.HTTP_400_BAD_REQUEST: RESPONSE_400,
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401,
        s.HTTP_409_CONFLICT: RESPONSE_409,
    },
)
async def start_interview(
    controller: Annotated[IInterviewController, Depends(get_interview_controller)],
    user: UserDTO = Depends(get_access_user),
):
    return await controller.start(user_id=user.id)

@router.post(
    "/{session_id}/answer",
    status_code=s.HTTP_200_OK,
    response_model=Dict[str, Any],
    responses={
        s.HTTP_200_OK: {
            "description": "Answer processed",
            "content": {
                "application/json": {
                    "examples": {
                        "need_followup": {
                            "summary": "Follow-up needed",
                            "value": {
                                "status": "need_followup",
                                "feedback": "Good start, but mention memory management specifics.",
                                "followup_question": {
                                    "interview_question_id": 777,
                                    "text": "How is stack memory allocated and freed?"
                                },
                                "followup_count": 1,
                                "followup_limit": 2
                            }
                        },
                        "final": {
                            "summary": "Main question completed",
                            "value": {
                                "status": "final",
                                "result": "satisfactory",
                                "feedback": "Solid explanation with correct tradeoffs.",
                                "next_question": {
                                    "interview_question_id": 502,
                                    "question_id": 1002,
                                    "text": "Explain how a hash table handles collisions."
                                },
                                "main_question_index": 2,
                                "total_main_questions": 10
                            }
                        },
                        "completed": {
                            "summary": "Interview completed",
                            "value": {
                                "status": "completed"
                            }
                        }
                    }
                }
            }
        },
        s.HTTP_400_BAD_REQUEST: RESPONSE_400,
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401,
    },
)
async def answer_interview_question(
    controller: Annotated[IInterviewController, Depends(get_interview_controller)],
    session_id: int,
    interview_question_id: int = Form(...),
    audio: UploadFile = File(...),
    user: UserDTO = Depends(get_access_user),
):
    data = await audio.read()
    filename = audio.filename or "audio.wav"
    return await controller.answer(
        session_id=session_id,
        interview_question_id=interview_question_id,
        audio=data,
        filename=filename,
        user_id=user.id,
        content_type=audio.content_type,
    )

@router.get(
    "/{session_id}",
    status_code=s.HTTP_200_OK,
    response_model=Dict[str, Any],
    responses={
        s.HTTP_200_OK: {
            "description": "Interview session status",
            "content": {
                "application/json": {
                    "example": {
                        "session_id": 12,
                        "status": "active",
                        "current_main_index": 3,
                        "total_main_questions": 10
                    }
                }
            }
        },
        s.HTTP_400_BAD_REQUEST: RESPONSE_400,
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401,
    },
)
async def get_interview_session(
    controller: Annotated[IInterviewController, Depends(get_interview_controller)],
    session_id: int,
    user: UserDTO = Depends(get_access_user),
):
    return await controller.get_session(session_id=session_id, user_id=user.id)
