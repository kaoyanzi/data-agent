import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState, MetricInfoStata
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


async def filter_metric(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    """
    为了把不需要的指标进行删除
    :param state:
    :param runtime:
    :return:
    """
    writer = runtime.stream_writer
    try:
        writer({"type":"progress","step":"过滤指标","status":"running"})
        metric_infos:list[MetricInfoStata] = state["metric_infos"]
        query = state["query"]
        prompt = PromptTemplate(template=load_prompt("filter_metric_info"),input_variables=["query","metric_infos"])
        chain = prompt | llm | JsonOutputParser()
        result = await chain.ainvoke({"query":query,"metric_infos":yaml.dump(metric_infos,allow_unicode=True,sort_keys=False)})
        #在循环中删除列表可能会造成漏删    解决办法:通过切片表达式[:]复制一份列表用作循环
        for metric_info in metric_infos[:]:
            if metric_info["name"] not in result:
                metric_infos.remove(metric_info)
        writer({"type":"progress","step":"过滤指标","status":"success"})
        logger.info("过滤指标成功:{}",metric_infos)
        return {"metric_infos":metric_infos}
    except Exception as e:
        logger.error(str(e))
        writer({"type": "progress", "step": "过滤指标", "status": "failed"})
        raise e
