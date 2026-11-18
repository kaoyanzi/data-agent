import asyncio

from langchain_huggingface import HuggingFaceEndpointEmbeddings
from sqlalchemy.dialects.oracle import vector

from app.conf.app_config import EmbeddingConfig, app_config


class EmbeddingClientManager:
    def __init__(self,config:EmbeddingConfig):
        self.config = config
        self.embedding_client:HuggingFaceEndpointEmbeddings = None
    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"
    def init(self):
        self.embedding_client = HuggingFaceEndpointEmbeddings(model=self._get_url())

embedding_client_manager = EmbeddingClientManager(app_config.embedding)

if __name__ == "__main__":
    embedding_client_manager.init()
    embedding_client = embedding_client_manager.embedding_client
    def test_sync():
        # vector:list[float] = embedding_client.embed_query("苹果")
        # print(vector)
        vectors:list[list[float]] = embedding_client.embed_documents(["苹果","香蕉"])
        print(vectors)
    # test_sync()
    async def test_async():
        # result:list[float] = await embedding_client.aembed_query("计算机")
        # print(result)
        # vectors:list[list[float]] = await embedding_client.aembed_documents(["电脑","计算机"])
        # print(vectors)

        #如果存在对大量的文本转向量,我们要进行分批次处理 每次处理3个
        vectors:list[list[float]] = []
        batch_size = 3
        texts = ["香蕉","苹果","葡萄","计算","计算器","书包","你好"]
        for i in range(0, len(texts), batch_size):
            print(f"{i}的值")
            #获取本批次处理的文本
            batch_texts = texts[i:i+batch_size]
            #异步转向量
            embedded = await embedding_client.aembed_documents(batch_texts)
            vectors.extend(embedded)
        print(vectors)
    asyncio.run(test_async())