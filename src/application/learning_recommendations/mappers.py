from typing import Optional

from src.application.learning_recommendations.dtos import LearningRecommendationDTO
from src.application.learning_recommendations.models import LearningRecommendation


def learning_recommendation_orm_to_dto(
    row: LearningRecommendation,
) -> Optional[LearningRecommendationDTO]:
    if row is None:
        return None

    return LearningRecommendationDTO(
        id=row.id,
        skill_id=row.skill_id,
        source=row.source,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def learning_recommendation_dto_to_orm(
    dto: LearningRecommendationDTO,
    row: Optional[LearningRecommendation] = None,
) -> LearningRecommendation:
    row = row or LearningRecommendation()

    if dto.skill_id is not None:
        row.skill_id = dto.skill_id
    if dto.source is not None:
        row.source = dto.source

    return row
