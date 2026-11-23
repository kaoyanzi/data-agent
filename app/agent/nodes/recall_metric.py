from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.entities.metric_info import MetricInfo
from app.prompt.prompt_loader import load_prompt


async def recall_metric(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    try:
        writer({"type":"progress","step":"召回指标","status":"running"})
        keywords = state["keywords"]
        prompt = PromptTemplate(template=load_prompt("extend_keywords_for_metric_recall"),input_variables=["query"])
        chain = prompt | llm | JsonOutputParser()
        result:list[str] = await chain.ainvoke({"query":state["query"]})
        keywords = list(set(result + keywords))

        retrieved_metrics_dict:dict[str,MetricInfo] = {}
        embedding_client = runtime.context["embedding_client"]
        metric_qdrant_repository = runtime.context["metric_qdrant_repository"]
        # for keyword in keywords:
        #     vector:list[float] = await embedding_client.aembed_query(keyword)
        #     metric_infos:list[MetricInfo] =await metric_qdrant_repository.search(vector)
        #     for metric_info in metric_infos:
        #         if metric_info.id not in retrieved_metrics_dict:
        #             retrieved_metrics_dict[metric_info.id] = metric_info
        vectors:list[list[float]] = await embedding_client.aembed_documents(keywords)
        metric_infos:list[MetricInfo] =await metric_qdrant_repository.search_batch(vectors)
        for metric_info in metric_infos:
            if metric_info.id not in retrieved_metrics_dict:
                retrieved_metrics_dict[metric_info.id] = metric_info
        writer({"type":"progress","step":"召回指标","status":"success"})
        logger.info("召回指标成功:{}", list(retrieved_metrics_dict.keys()))
        # 更新state状态
        return {"retrieved_metrics": list(retrieved_metrics_dict.values())}
    except Exception as e:
        logger.error(str(e))
        writer({"type": "progress", "step": "召回指标", "status": "failed"})
        raise e
