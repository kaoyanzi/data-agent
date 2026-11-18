import asyncio
import uuid
from enum import Enum
from typing import Optional

from aiohttp import payload
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct, QueryResponse

from app.clients.embedding_client_manager import embedding_client_manager
from app.conf.app_config import QdrantConfig, app_config


class QdrantClientManager:

    def __init__(self,config:QdrantConfig):
        self.config = config
        self.client: Optional[AsyncQdrantClient] = None

    def _geturl(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        self.client = AsyncQdrantClient(url=self._geturl())

    async def close(self):
        if self.client:
            await self.client.close()

qdrant_client_manager = QdrantClientManager(config=app_config.qdrant)

if __name__ == "__main__":
    qdrant_client_manager.init()
    qdrant_client = qdrant_client_manager.client
    embedding_client_manager.init()
    embedding_client = embedding_client_manager.embedding_client
    # class Color(Enum):
    #     RED = 1
    #     GREEN = 2
    #     BLUE = 3
    #
    #
    # print(Color.RED.value)
    # print(Color.BLUE)
    # print(Color.GREEN)

    async def test_collection():
        result = await qdrant_client.collection_exists(
            collection_name="test1",
        )
        print(result)
        if result:
            #如果存在先删除
            await qdrant_client.delete_collection(collection_name="test1")
            #新建集合
            result = await qdrant_client.create_collection(
                collection_name="test1_1",
                vectors_config=VectorParams(
                    size=1024,
                    distance=Distance.COSINE
                )
            )
            print(result)


        await qdrant_client_manager.close()
    # asyncio.run(test_collection())
    async def test_vector():
        await qdrant_client.upsert(
            collection_name="test1_1",
            points=[
                PointStruct(
                    id= uuid.uuid4(),
                    vector=await embedding_client.aembed_query("苹果"),
                    payload={"keyword":"苹果","category":"水果"}
                ),
                PointStruct(
                    id=uuid.uuid4(),
                    vector=await embedding_client.aembed_query("香蕉"),
                    payload={"keyword": "香蕉", "category": "水果"}
                ),
                PointStruct(
                    id=uuid.uuid4(),
                    vector=await embedding_client.aembed_query("程序员"),
                    payload={"keyword": "程序员", "category": "岗位"}
                ),
            ]
        )
    # asyncio.run(test_vector())
    async def test_search(query:str,score:float=0.5,limit:int=5) -> list:
        result:QueryResponse = await qdrant_client.query_points(
            collection_name="test1_1",
            query=await embedding_client.aembed_query(query),
            score_threshold=score,#最小值得分
            limit=limit,
        )
        return [point.payload for point in result.points]

    async def main():
        r1 = await asyncio.gather(test_search("芒果"),test_search("研发人员"))
        print(r1)

    asyncio.run(main())