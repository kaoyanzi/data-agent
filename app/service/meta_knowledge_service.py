import uuid
from pathlib import Path
from typing import Any

from langchain_huggingface import HuggingFaceEndpointEmbeddings
from omegaconf import OmegaConf

from app.conf.meta_config import MetaConfig, TableConfig, MetricConfig
from app.core.log import logger
from app.entities import value_info, column_info
from app.entities.column_info import ColumnInfo
from app.entities.column_metric import ColumnMetric
from app.entities.metric_info import MetricInfo
from app.entities.table_info import TableInfo
from app.entities.value_info import ValueInfo
from app.repositories.es.value_es_repository import ValueInfoRepository
from app.repositories.mysql.dw_mysql_repository import DwMysqlRepository
from app.repositories.mysql.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repositoty import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class MetaKnowledgeService:
    """
    用于构建元数据知识库业务逻辑处理
    """
    def __init__(self,metric_qdrant_repository:MetricQdrantRepository,value_info_repository:ValueInfoRepository,column_qdrant_repository:ColumnQdrantRepository,embedding_client:HuggingFaceEndpointEmbeddings,dw_mysql_repository:DwMysqlRepository,meta_mysql_repository:MetaMysqlRepository):
        self.dw_mysql_repository = dw_mysql_repository
        self.meta_mysql_repository = meta_mysql_repository
        self.embedding_client = embedding_client
        self.column_qdrant_repository = column_qdrant_repository
        self.value_info_repository = value_info_repository
        self.metric_qdrant_repository = metric_qdrant_repository

    async def bulid(self, meta_config_path:Path):
        logger.info("业务层被调用:{}",meta_config_path)
        #1.解析yaml文件,封装为dataclass对象 -> MetaConfig
        #1.1加载yaml文件得到OmegaConf对象
        content = OmegaConf.load(meta_config_path)
        #1.2加载MetaConfig_dataclass得到OmegaConf对象
        structured = OmegaConf.structured(MetaConfig)
        #1.3将两者合并后再转为dataclass对象
        meta_config:MetaConfig = OmegaConf.to_object(OmegaConf.merge(structured, content))
        logger.info(meta_config)

        #2.处理表格信息
        if meta_config.tables:
            # 2.1 将表以及表中包含的字段信息传入源数据库meta库
            column_infos:list[ColumnInfo] = await self._save_table_infos_to_meta_db(meta_config.tables)
            logger.info("将表/字段信息存入meta数据库成功")
            # 2.2 将字段信息建立向量索引 字段名称,描述,别名 存储到qdrant向量库中
            await self._sava_column_info_to_qdrant(column_infos)
            logger.info("为字段信息建立向量索引成功")
            # 2.3将字段的取值建立全文索引 字段所有取值  存入Elasticsearch全文库
            await self.save_column_info_to_es(meta_config.tables,column_infos)
            logger.info("为字段信息建立全文索引成功")
        # #3.处理指标信息
        if meta_config.metrics:
            #3.1 将指标信息存入meta库
            metric_infos:list[MetricInfo] = await self._save_metric_info_to_meta_db(meta_config.metrics)
            logger.info("将指标信息存入meta数据库成功")
            #3.2为指标建立向量索引 指标名称,描述,别名 存储到qdrant向量库中
            await self._save_metric_info_to_qdrant(metric_infos)
            logger.info("为指标信息建立向量索引成功")


    async def _save_table_infos_to_meta_db(self, tables:list[TableConfig]) -> list[ColumnInfo]:
        table_infos:list[TableInfo] = []
        column_infos:list[ColumnInfo] = []

        for table_config in tables:
            table_info = TableInfo(
                id = table_config.name,
                name = table_config.name,
                role=table_config.role,
                description = table_config.description,
            )
            table_infos.append(table_info)

            #调用数据仓库的持久层根据表的di查询表字段的数据类型 返回字典:{字段名称:数据类型}
            column_type_dict:dict[str,str]  =await self.dw_mysql_repository.get_column_type_by_table_id(table_info.id)
            for column_config in table_config.columns:
                examples:list[str] = await self.dw_mysql_repository.get_column_values(table_info.id, column_config.name)
                column_info = ColumnInfo(
                    id = f"{table_info.name}.{column_config.name}",
                    name = column_config.name,
                    role = column_config.role,
                    description = column_config.description,
                    alias=column_config.alias,
                    table_id=table_info.id,
                    type=column_type_dict[column_config.name],
                    examples=examples,
                )
                column_infos.append(column_info)



        await self.meta_mysql_repository.save_table_infos(table_infos)
        await self.meta_mysql_repository.save_column_infos(column_infos)
        # 返回字段信息用于构建向量加全文索引
        return column_infos

    async def _sava_column_info_to_qdrant(self, column_infos:list[ColumnInfo]):
        #1.确保字段向量集合存在
        await self.column_qdrant_repository.ensure_collection()
        #2.构建向量点的三项信息
        #2.1声明一个存放向量点的列表
        points:list[dict] = []
        #2.2遍历字段的列表,构建向量点字典:id,转向量的文本,字段的信息
        for column_info in column_infos:
            points.append({
                    "id": uuid.uuid4(),
                    "embedding_text": column_info.name,
                    "payload": column_info
            })
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": column_info.description,
                "payload": column_info
            })
            for alias in column_info.alias:
                points.append({
                    "id": uuid.uuid4(),
                    "embedding_text": alias,
                    "payload": column_info
                })
        #2.3分批次对所有文本转向量化
        embeddeds:list[float] = []
        embedding_texts = [point["embedding_text"] for point in points]
        batch_size = 10
        for i in range(0, len(embedding_texts), batch_size):
            batch_embedding_text = embedding_texts[i:i+batch_size]
            batch_embedded = await self.embedding_client.aembed_documents(batch_embedding_text)
            embeddeds.extend(batch_embedded)


        #3.调用持久层 批量新增
        ids = [point["id"] for point in points]
        payloads = [point["payload"] for point in points]
        await self.column_qdrant_repository.upsert(ids,payloads,embeddeds)

    async def save_column_info_to_es(self, table_configs:list[TableConfig], column_infos:list[ColumnInfo]):
        """准备es持久层需要的数据"""
        #1.创建索引库手动指定映射 确保索引库存在
        await self.value_info_repository.ensure_index()

        #2.获取字段取值信息
        value_infos:list[ValueInfo] = []
        #2.1从yaml中获取需要将字段取值建立全文索引的字段名称列表
        need_sync_to_es = [column.name for table in table_configs for column in table.columns if column.sync is True]
        #2.2遍历字段信息的列表
        for column_info in column_infos:
            column_name = column_info.name
            if column_name in need_sync_to_es:
                #2.2.1根据表id加字段名称获取字段的所有取值
                column_values:list[str] = await self.dw_mysql_repository.get_column_values(column_info.table_id, column_name,limit=1000000)
                #2.2.2构建ValueInfo对象
                for column_value in column_values:
                    value_info = ValueInfo(
                        id = f"{column_info.id}.{column_value}",
                        value = column_value,
                        column_id = column_info.id,
                    )
                    value_infos.append(value_info)
        #3.调用es持久层批量的新增文档到索引库
        await self.value_info_repository.upsert(value_infos)

    async def _save_metric_info_to_meta_db(self, metrics:list[MetricConfig]) -> list[MetricInfo]:
        metric_infos:list[MetricInfo] = []
        column_metric_infos:list[ColumnMetric] = []
        for metric_config in metrics:
            metric_info = MetricInfo(
                id = metric_config.name,
                name = metric_config.name,
                description = metric_config.description,
                relevant_columns=metric_config.relevant_columns,
                alias=metric_config.alias,
            )
            metric_infos.append(metric_info)
            for relevant_column in metric_config.relevant_columns:
                column_info = ColumnMetric(
                    column_id=relevant_column,
                    metric_id=metric_info.id,
                )
                column_metric_infos.append(column_info)

        await self.meta_mysql_repository.save_metric_infos(metric_infos)
        await self.meta_mysql_repository.save_column_metric_infos(column_metric_infos)
        return metric_infos

    async def _save_metric_info_to_qdrant(self, metric_infos:list[MetricInfo]):
        #1.确保指标向量集合存在
        await self.metric_qdrant_repository.ensure_collection()
        # 2.构建向量点的三项信息
        # 2.1声明一个存放向量点的列表
        points:list[dict[str,Any]] = []
        for metric_info in metric_infos:
            points.append({
                "id": uuid.uuid4(),
                "payload": metric_info,
                "embedding_text": metric_info.name
            })
            points.append({
                "id": uuid.uuid4(),
                "payload": metric_info,
                "embedding_text": metric_info.description
            })
            for alias in metric_info.alias:
                points.append({
                    "id": uuid.uuid4(),
                    "payload": metric_info,
                    "embedding_text": alias,
                })
        batch_size = 10
        embeddeds:list[float] = []
        embedding_texts = [point["embedding_text"] for point in points]
        for i in range(0, len(points), batch_size):
            batch_embedding_text = embedding_texts[i:i+batch_size]
            batch_embedded = await self.embedding_client.aembed_documents(batch_embedding_text)
            embeddeds.extend(batch_embedded)
        ids = [point["id"] for point in points]
        payloads = [point["payload"] for point in points]
        await self.metric_qdrant_repository.upsert(ids,payloads,embeddeds)