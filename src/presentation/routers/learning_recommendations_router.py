from typing import Annotated, Dict, Any

from fastapi import APIRouter, status as s, Depends

from src.application.learning_recommendations.interfaces import ILearningRecommendationController
from src.application.users.dtos import UserDTO
from src.domain.responses import RESPONSE_401, RESPONSE_404, RESPONSE_408
from src.presentation.depends.controllers import get_learning_recommendation_controller
from src.presentation.depends.security import get_access_user

router = APIRouter(
    prefix="/learning-recommendations",
    tags=["learning_recommendations"],
)


@router.get(
    "/ai/{skill_id}",
    summary="Get learning recommendations",
    status_code=s.HTTP_200_OK,
    response_model=Dict[str, Any],
    responses={
        s.HTTP_200_OK: {
            "description": "Learning recommendations",
            "content": {
                "application/json": {
                    "example": {
                        "skill_id": 12,
                        "sources": [
                            "https://example.com/resource-1",
                            "https://example.com/resource-2",
                        ],
                    }
                }
            },
        },
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401,
        s.HTTP_404_NOT_FOUND: RESPONSE_404,
        s.HTTP_408_REQUEST_TIMEOUT: RESPONSE_408,
    },
)
async def get_learning_recommendations(
    skill_id: int,
    controller: Annotated[ILearningRecommendationController, Depends(get_learning_recommendation_controller)],
    user: UserDTO = Depends(get_access_user),
):
    return await controller.get_recommendations(user_id=user.id, skill_id=skill_id)
