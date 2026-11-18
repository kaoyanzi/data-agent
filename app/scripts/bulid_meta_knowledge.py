import argparse
import asyncio
from pathlib import Path
from sys import argv


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
    meta_knowledge_service = MetaKnowledgeService()
    await meta_knowledge_service.bulid(meta_config_path)


if __name__ == "__main__":
    asyncio.run(bulid())