from typing import Optional, List

from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk

from src.application.directions.dtos import DirectionDTO, ProgressStatisticsDTO
from src.application.directions.interfaces import IDirectionStatisticsService
from src.application.modules.interfaces import IModuleStatisticsService
from src.application.skills.interfaces import IUserSkillRepository
from src.domain.base_dto import PaginationDTO


class DirectionSearchService:

    INDEX_NAME = "directions_index"

    def __init__(self, es_client: AsyncElasticsearch):
        self._es = es_client

    # -----------------------------
    # INDEX CREATION
    # -----------------------------
    async def create_index_if_not_exists(self) -> None:
        exists = await self._es.indices.exists(index=self.INDEX_NAME)

        if exists:
            return

        await self._es.indices.create(
            index=self.INDEX_NAME,
            settings={
                "index": {
                    "max_ngram_diff": 18  # max_gram - min_gram
                },
                "analysis": {
                    "analyzer": {
                        "autocomplete_analyzer": {
                            "tokenizer": "ngram_tokenizer",
                            "filter": ["lowercase"]
                        }
                    },
                    "tokenizer": {
                        "ngram_tokenizer": {
                            "type": "ngram",
                            "min_gram": 2,
                            "max_gram": 20,
                            "token_chars": ["letter", "digit"]
                        }
                    }
                }
            },
            mappings={
                "properties": {
                    "name": {
                        "type": "text",
                        "analyzer": "autocomplete_analyzer",
                        "search_analyzer": "standard"
                    }
                }
            }
        )

    async def delete_index(self) -> bool:
        try:
            exists = await self._es.indices.exists(index=self.INDEX_NAME)

            if not exists:
                return False

            await self._es.indices.delete(index=self.INDEX_NAME)
            return True

        except Exception:
            return False

    # -----------------------------
    # COUNT
    # -----------------------------
    async def count(self) -> int:
        try:
            response = await self._es.count(index=self.INDEX_NAME)
            return response["count"]
        except Exception:
            return -1

    # -----------------------------
    # BULK INDEX
    # -----------------------------
    async def bulk_index(self, directions: List[DirectionDTO]) -> None:
        if not directions:
            return

        actions = [
            {
                "_index": self.INDEX_NAME,
                "_id": direction.id,
                "_source": {
                    "id": direction.id,
                    "name": direction.name,
                },
            }
            for direction in directions
            if direction.id is not None and direction.name
        ]

        if not actions:
            return

        await async_bulk(self._es, actions, refresh=True)

    # -----------------------------
    # SINGLE INDEX
    # -----------------------------
    async def index(self, direction_id: int, name: str):
        await self._es.index(
            index=self.INDEX_NAME,
            id=direction_id,
            document={
                "id": direction_id,
                "name": name,
            }
        )

    # -----------------------------
    # DELETE
    # -----------------------------
    async def delete(self, direction_id: int):
        await self._es.delete(
            index=self.INDEX_NAME,
            id=direction_id,
            ignore=[404],
        )

    # -----------------------------
    # SEARCH
    # -----------------------------
    async def search(
            self,
            name: Optional[str] = None,
            pagination: Optional[PaginationDTO[DirectionDTO]] = None,
    ) -> PaginationDTO[DirectionDTO]:

        pagination = pagination or PaginationDTO[DirectionDTO]()

        page = max(pagination.page or 1, 1)
        per_page = max(pagination.per_page or 10, 1)

        from_value = (page - 1) * per_page

        query_body = {
            "from": from_value,
            "size": per_page,
            "query": {"match_all": {}},
        }

        if name:
            query_body["query"] = {
                "bool": {
                    "should": [
                        {
                            "match": {
                                "name": {
                                    "query": name,
                                    "fuzziness": "AUTO",
                                }
                            }
                        }
                    ]
                }
            }

        response = await self._es.search(
            index=self.INDEX_NAME,
            body=query_body,
        )

        total = response["hits"]["total"]["value"]
        hits = response["hits"]["hits"]

        items: List[DirectionDTO] = [
            DirectionDTO(
                id=hit["_source"]["id"],
                name=hit["_source"]["name"],
            )
            for hit in hits
        ]

        return PaginationDTO[DirectionDTO](
            page=page,
            per_page=per_page,
            total=total,
            items=items,
        )


class DirectionStatisticsService(IDirectionStatisticsService):
    def __init__(
        self,
        module_statistics_service: IModuleStatisticsService,
        user_skill_repository: IUserSkillRepository,
    ):
        self._module_statistics_service = module_statistics_service
        self._user_skill_repository = user_skill_repository

    async def get_statistics(
        self,
        user_id: int,
    ) -> ProgressStatisticsDTO:

        modules = await self._user_skill_repository.get_by_user_id(
            user_id=user_id,
            to_learn=True,
        )
        skills = modules.items or []

        total_questions = 0
        met_questions = 0
        correct_answers = 0
        incorrect_answers = 0

        for module in skills:
            if module.skill_id is None:
                continue

            stats = await self._module_statistics_service.get_statistics(
                user_id=user_id,
                module_id=module.skill_id,
            )

            total_questions += stats.total_questions or 0
            met_questions += stats.met_questions or 0
            correct_answers += stats.correct_answers or 0
            incorrect_answers += stats.incorrect_answers or 0

        readiness_percentage = 0.0
        if total_questions > 0:
            readiness_percentage = (correct_answers / total_questions) * 100

        return ProgressStatisticsDTO(
            total_questions=total_questions,
            met_questions=met_questions,
            correct_answers=correct_answers,
            incorrect_answers=incorrect_answers,
            readiness_percentage=readiness_percentage,
        )
