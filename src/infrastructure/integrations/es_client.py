from elasticsearch import AsyncElasticsearch


class ElasticsearchClient:

    def __init__(self, host: str):
        self._client = AsyncElasticsearch(hosts=[host])

    @property
    def client(self) -> AsyncElasticsearch:
        return self._client

    async def close(self):
        await self._client.close()
