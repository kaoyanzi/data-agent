import asyncio
from typing import Optional

from elastic_transport import ObjectApiResponse
from elasticsearch import AsyncElasticsearch

from app.conf.app_config import ESConfig, app_config


class EsClientManager:

    def __init__(self,config:ESConfig):
        self.config = config
        self.client:Optional[AsyncElasticsearch] = None

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        self.client = AsyncElasticsearch(hosts=self._get_url())

    async def close(self):
        if self.client:
            await self.client.close()

es_client_manager = EsClientManager(app_config.es)

if __name__ == "__main__":
    es_client_manager.init()
    es_client = es_client_manager.client

    async def test_index():
       result = await es_client.indices.exists(index="goods")
       print(result)
       if not result:
            await es_client.indices.create(
               index="goods",
               mappings={
                   "properties": {
                       "title": {"type": "text","analyzer": "ik_max_word","search_analyzer": "ik_max_word"},
                       "brand": {"type": "keyword"},
                       "images": {"type": "keyword","index": False},
                       "price": {"type": "integer"},
                   }
               }
            )
       await es_client_manager.close()
    # asyncio.run(test_index())

    async def test_doc():
        result:ObjectApiResponse = await es_client.bulk(
            index="goods",
            operations=[
                {
                    "index": {
                        "_index": "goods",
                    }
                },
                {
                    "name": "Revelation Space",
                    "author": "Alastair Reynolds",
                    "release_date": "2000-03-15",
                    "page_count": 585
                },
                {
                    "index": {
                        "_index": "goods"
                    }
                },
                {
                    "name": "1984",
                    "author": "George Orwell",
                    "release_date": "1985-06-01",
                    "page_count": 328
                },
                {
                    "index": {
                        "_index": "goods"
                    }
                },
                {
                    "name": "Fahrenheit 451",
                    "author": "Ray Bradbury",
                    "release_date": "1953-10-15",
                    "page_count": 227
                },
                {
                    "index": {
                        "_index": "goods"
                    }
                },
                {
                    "name": "Brave New World",
                    "author": "Aldous Huxley",
                    "release_date": "1932-06-01",
                    "page_count": 268
                },
                {
                    "index": {
                        "_index": "goods"
                    }
                },
                {
                    "name": "The Handmaids Tale",
                    "author": "Margaret Atwood",
                    "release_date": "1985-06-01",
                    "page_count": 311
                }
            ]
        )
        print(result)
        await es_client_manager.close()

    asyncio.run(test_doc())
