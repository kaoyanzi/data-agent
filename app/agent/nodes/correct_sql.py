from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime
import yaml

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState, TableInfoStata, MetricInfoStata, DateInfoState, DBInfoState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


async def correct_sql(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    try:
        writer({"type":"process","step":"修正SQL","state":"running"})
        modify_count = state.get("modify_count",0)
        if modify_count >= 3:
            raise Exception("SQL修复次数到达三次,终止流程")
        query = state["query"]
        table_infos: list[TableInfoStata] = state["table_infos"]
        metric_infos: list[MetricInfoStata] = state["metric_infos"]
        date_info: DateInfoState = state["date_info"]
        db_info: DBInfoState = state["db_info"]
        sql = state["sql"]
        error = state["error"]
        prompt = PromptTemplate(template=load_prompt("correct_sql"),input_variables=["sql","error","query","table_infos","metric_infos","date_info","db_info"])
        chain = prompt | llm | StrOutputParser()
        new_sql = await chain.ainvoke({
            "query": query,
            "table_infos": yaml.dump(table_infos, allow_unicode=True, sort_keys=False),
            "metric_infos": yaml.dump(metric_infos, allow_unicode=True, sort_keys=False),
            "date_info": yaml.dump(date_info, allow_unicode=True, sort_keys=False),
            "db_info": yaml.dump(db_info, allow_unicode=True, sort_keys=False),
            "sql": sql,
            "error": error,
        })
        writer({"type":"process","step":"修正SQL","state":"success"})
        logger.info("修复后的SQL:{}",new_sql)
        return {"sql":new_sql,"modify_count":modify_count+1}
    except Exception as e:
        logger.error(str(e))
        writer({"type": "process", "step": "修正SQL", "state": "failed"})
        raise e
