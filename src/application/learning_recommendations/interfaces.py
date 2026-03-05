from abc import ABC, abstractmethod
from typing import List

from src.application.learning_recommendations.dtos import LearningRecommendationDTO


class ILearningRecommendationRepository(ABC):
    @abstractmethod
    async def add_many(self, dtos: List[LearningRecommendationDTO]) -> List[LearningRecommendationDTO]: ...

    @abstractmethod
    async def get_by_skill_id(self, skill_id: int) -> List[LearningRecommendationDTO]: ...


class ILearningRecommendationController(ABC):
    @abstractmethod
    async def get_recommendations(self, user_id: int, skill_id: int) -> dict: ...
