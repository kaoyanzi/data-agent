
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.entities.value_info import ValueInfo
from app.prompt.prompt_loader import load_prompt


async def recall_value(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    try:
        writer({"type":"progress","step":"召回字段取值","status":"running"})
        #扩充关键词
        prompt = PromptTemplate(template=load_prompt("extend_keywords_for_value_recall"),input_variables=["query"])
        chain = prompt | llm | JsonOutputParser()
        result = await chain.ainvoke({"query":state["query"]})
        keywords = list(set(state["keywords"]+result))

        #执行es全文检索
        retrieved_value_dict:dict[str, ValueInfo] = {}
        value_info_repository = runtime.context["value_info_repository"]
        for keyword in keywords:
            value_infos:list[ValueInfo] = await value_info_repository.search(keyword)
            logger.info("es search keyword:{} hits:{}", keyword, len(value_infos))
            # 解析结果
            for value_info in value_infos:
                if value_info.id not in retrieved_value_dict:
                    retrieved_value_dict[value_info.id] = value_info
        #更新state
        writer({"type":"progress","step":"召回字段取值","status":"success"})
        logger.info(f"召回字段取值成功：{list(retrieved_value_dict.values())}")
        return {"retrieved_values":list(retrieved_value_dict.values())}
    except Exception as e:
        logger.error(str(e))
        writer({"type": "progress", "step": "召回字段取值", "status": "failed"})
        raise e
