from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.entities.column_info import ColumnInfo
from app.prompt.prompt_loader import load_prompt


async def recall_column(state: DataAgentState,runtime:Runtime[DataAgentContext]):
    logger.info("召回字段节点")
    writer = runtime.stream_writer
    try:
        writer({"type":"process","step":"召回字段","status":"running"})
        keywords = state["keywords"]
        #调用大预言模型,对用户的问题进行一个扩充回答问题可能用到的(中文语义)字段列表,得到关键词列表
        prompt = PromptTemplate(template=load_prompt('extend_keywords_for_column_recall'),input_variables=["query"])
        chain = prompt | llm | JsonOutputParser()
        result:list[str] = await chain.ainvoke({"query":state["query"]})
        keywords = list(set(result + keywords))
        #查询qdrant数据库字段信息的集合
        embedding_client = runtime.context["embedding_client"]
        column_qdrant_repository = runtime.context["column_qdrant_repository"]
        retrieved_column_infos_dict:dict[str,ColumnInfo] = {}   #key是字段id,value是字段信息对象
        for keyword in keywords:
            vector:list[float] = await embedding_client.aembed_query(keyword)
            column_infos:list[ColumnInfo] = await column_qdrant_repository.search(vector)
            #结果去重,避免重复的字段信息
            for column_info in column_infos:
                if column_info.id not in retrieved_column_infos_dict:
                    retrieved_column_infos_dict[column_info.id] = column_info
        writer({"type":"process","step":"召回字段","status":"success"})
        logger.info("召回字段成功:{}",list(retrieved_column_infos_dict.keys()))
        #更新state状态
        return {"retrieved_columns":list(retrieved_column_infos_dict.values())}
    except Exception as e:
        writer({"type": "process", "step": "召回字段", "status": "failed"})
        raise e
