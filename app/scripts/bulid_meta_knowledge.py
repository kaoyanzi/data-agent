import argparse
import asyncio
from pathlib import Path
from sys import argv

from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import dw_mysql_client_manager, meta_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.repositories.es.value_es_repository import ValueInfoRepository
from app.repositories.mysql.dw_mysql_repository import DwMysqlRepository
from app.repositories.mysql.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant import column_qdrant_repositoty
from app.repositories.qdrant.column_qdrant_repositoty import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.service.meta_knowledge_service import MetaKnowledgeService


async def bulid():
    #1. 获取脚本参数中人工补齐的yaml文件 方式1:argv严格的按索引获取 方式2:argparse(底层也是argv)
    #1.1创建ArgumentParser对象
    parser = argparse.ArgumentParser(
        description="用于构建元数据知识库",
        usage="python -m app.scripts.bulid_meta_knowledge -c xxx.yaml",
        epilog="-------------------end------------------"
    )
    #1.2添加要求传入的脚本参数 通过短选项或者长选项传入动态参数
    parser.add_argument("-c","--conf")
    #1.3调用解析参数的方法   结果被封装Namespace对象中:长选项参数名作为属性名称
    args = parser.parse_args()
    #1.4将yaml文件的路径转为Path对象
    meta_config_path = Path(args.conf)
    #2.调用业务层
    #2.1执行各个客服端初始化操作
    dw_mysql_client_manager.init()
    meta_mysql_client_manager.init()
    embedding_client_manager.init()
    qdrant_client_manager.init()
    es_client_manager.init()
    #2,2 创建各个持久层对象
    async with dw_mysql_client_manager.session_factory() as dw_session,meta_mysql_client_manager.session_factory() as meta_session:
        #2.3创造业务层对象,通过构造注入各个持久层对象
        meta_knowledge_service = MetaKnowledgeService(
            dw_mysql_repository = DwMysqlRepository(dw_session),
            meta_mysql_repository = MetaMysqlRepository(meta_session),
            embedding_client = embedding_client_manager.embedding_client,
            column_qdrant_repository = ColumnQdrantRepository(qdrant_client_manager.client),
            value_info_repository= ValueInfoRepository(es_client_manager.client),
            metric_qdrant_repository=MetricQdrantRepository(qdrant_client_manager.client)
        )
        #2.4调用业务逻辑
        await meta_knowledge_service.bulid(meta_config_path)

        #3提交事务,关闭各个客户端
        await meta_session.commit()

        await dw_mysql_client_manager.close()
        await meta_mysql_client_manager.close()
        await qdrant_client_manager.close()
        await es_client_manager.close()



if __name__ == "__main__":
    asyncio.run(bulid())