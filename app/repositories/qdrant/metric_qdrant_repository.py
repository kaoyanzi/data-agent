from dataclasses import asdict

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct, QueryResponse, QueryRequest

from app.conf.app_config import app_config
from app.entities.metric_info import MetricInfo


class MetricQdrantRepository:

    COLLECTION_NAME = 'data-agent-metric'

    def __init__(self,client:AsyncQdrantClient):
        self.client = client

    async def ensure_collection(self):
        # 创建向量集合
        if not await self.client.collection_exists(collection_name=self.COLLECTION_NAME):
            await self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=app_config.qdrant.embedding_size,
                    distance=Distance.COSINE
                )
            )

    async def upsert(self, ids:list[str], payloads:list[MetricInfo], embeddeds:list[list[float]],batch_size:int=10):
        zipped = list(zip(ids,payloads,embeddeds))
        for i in range(0,len(zipped),batch_size):
            batch = zipped[i:i+batch_size]
            points = [PointStruct(id=id,payload=asdict(payload),vector=embedded) for id,payload,embedded in zipped]
            await self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=points,
            )
    """单词查询"""
    async def search(self, vector:list[float], score_threshold:float=0.6, limit:int=10) -> list[MetricInfo]:
        result:QueryResponse = await self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=vector,
            score_threshold=score_threshold,
            limit=limit,
        )

        return [MetricInfo(**point.payload) for point in result.points]
    """批量查询"""
    async def search_batch(self, vectors: list[list[float]], score_threshold: float = 0.6, limit: int = 10) -> list[
        MetricInfo]:
        #将每个向量转为QueryRequest对象得到QueryResponse列表
        query_requests:list[QueryRequest] = [QueryRequest(
            query=vector,
            with_payload=True,
            score_threshold=score_threshold,
            limit=limit,
        ) for vector in vectors]
        results: list[QueryResponse] = await self.client.query_batch_points(
            collection_name=self.COLLECTION_NAME,
            requests=query_requests
        )

        return [MetricInfo(**point.payload) for result in results for point in result.points]

