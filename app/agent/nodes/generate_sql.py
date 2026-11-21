import yaml
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState, TableInfoStata, MetricInfoStata, DateInfoState, DBInfoState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


async def generate_sql(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    try:
        writer({"type":"process","step":"生成SQL","state":"running"})
        query = state["query"]
        table_infos:list[TableInfoStata] = state["table_infos"]
        metric_infos:list[MetricInfoStata] = state["metric_infos"]
        date_info:DateInfoState = state["date_info"]
        db_info:DBInfoState = state["db_info"]

        prompt = PromptTemplate(template=load_prompt("generate_sql"),input_variables=["query","table_infos","metric_infos","date_info","db_info"])
        chain = prompt | llm | StrOutputParser()
        sql = await chain.ainvoke({
            "query":query,
            "table_infos":yaml.dump(table_infos,allow_unicode=True,sort_keys=False),
            "metric_infos":yaml.dump(metric_infos,allow_unicode=True,sort_keys=False),
            "date_info":yaml.dump(date_info,allow_unicode=True,sort_keys=False),
            "db_info":yaml.dump(db_info,allow_unicode=True,sort_keys=False)
        })
        logger.info("生成的SQL:{}",sql)
        writer({"type":"process","step":"生成SQL","state":"success"})
        return {"sql":sql}
    except Exception as e:
        logger.error(str(e))
        writer({"type": "process", "step": "生成SQL", "state": "failed"})
        raise e
