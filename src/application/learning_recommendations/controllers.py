from typing import Dict, Any, List

from fastapi import HTTPException, status as s

from src.application.learning_recommendations.dtos import LearningRecommendationDTO
from src.application.learning_recommendations.interfaces import (
    ILearningRecommendationController,
    ILearningRecommendationRepository,
)
from src.application.skills.interfaces import ISkillRepository, IUserSkillRepository
from src.domain.interfaces import IUoW, IOpenAIService
from src.domain.value_objects import ChatGPTModel


class LearningRecommendationController(ILearningRecommendationController):
    def __init__(
        self,
        learning_recommendation_repository: ILearningRecommendationRepository,
        skill_repository: ISkillRepository,
        user_skill_repository: IUserSkillRepository,
        openai_service: IOpenAIService,
        uow: IUoW,
    ):
        self._learning_recommendation_repository = learning_recommendation_repository
        self._skill_repository = skill_repository
        self._user_skill_repository = user_skill_repository
        self._openai_service = openai_service
        self._uow = uow

    async def get_recommendations(self, user_id: int, skill_id: int) -> Dict[str, Any]:
        user_skill = await self._user_skill_repository.get_by_user_and_skill(
            user_id=user_id,
            skill_id=skill_id,
            populate_skill=True,
        )
        if user_skill is None or user_skill.to_learn is not True:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="Skill not found in user modules")

        skill_name = user_skill.skill.name if user_skill.skill else None
        if not skill_name:
            skill = await self._skill_repository.get_by_id(skill_id)
            if not skill or not skill.name:
                raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="Skill not found")
            skill_name = skill.name

        existing = await self._learning_recommendation_repository.get_by_skill_id(skill_id)
        if existing:
            return {
                "skill_id": skill_id,
                "sources": [r.source for r in existing if r.source],
            }

        sources: List[str] = []
        for _ in range(3):
            sources = await self._openai_service.get_learning_recommendations(
                skill_name=skill_name,
                model=ChatGPTModel.GPT_4_1,
            )
            if sources:
                break
        if not sources:
            raise HTTPException(
                status_code=s.HTTP_408_REQUEST_TIMEOUT,
                detail="Failed to generate recommendations, please try again",
            )

        dtos: List[LearningRecommendationDTO] = [
            LearningRecommendationDTO(skill_id=skill_id, source=source) for source in sources
        ]

        async with self._uow:
            created = await self._learning_recommendation_repository.add_many(dtos)

        return {
            "skill_id": skill_id,
            "sources": [r.source for r in created if r and r.source],
        }
