from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.learning_recommendations.dtos import LearningRecommendationDTO
from src.application.learning_recommendations.interfaces import ILearningRecommendationRepository
from src.application.learning_recommendations.mappers import (
    learning_recommendation_orm_to_dto,
    learning_recommendation_dto_to_orm,
)
from src.application.learning_recommendations.models import LearningRecommendation


class LearningRecommendationRepository(ILearningRecommendationRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add_many(self, dtos: List[LearningRecommendationDTO]) -> List[LearningRecommendationDTO]:
        rows = [learning_recommendation_dto_to_orm(dto) for dto in dtos]
        self._session.add_all(rows)

        await self._session.flush()
        for row in rows:
            await self._session.refresh(row)

        return [learning_recommendation_orm_to_dto(row) for row in rows]

    async def get_by_skill_id(self, skill_id: int) -> List[LearningRecommendationDTO]:
        query = select(LearningRecommendation).where(LearningRecommendation.skill_id == skill_id)
        result = await self._session.execute(query)
        rows = result.scalars().all()
        return [learning_recommendation_orm_to_dto(row) for row in rows]
