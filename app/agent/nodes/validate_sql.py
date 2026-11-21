from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def validate_sql(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    try:
        writer({"type":"process","step":"校验SQL","state":"running"})
        sql = state["sql"]
        if not sql:
            return {"error":"SQL为空"}
        if not sql.lower().startswith("select"):
            return {"error":"生成的SQL只能是select查询语句"}
        dw_mysql_repository= runtime.context["dw_mysql_repository"]
        await dw_mysql_repository.validate_sql(sql)
        writer({"type":"process","step":"校验SQL","state":"success"})
        return {"error":None}
    except Exception as e:
        logger.error(str(e))
        writer({"type": "process", "step": "校验SQL", "state": "failed"})
        return {"error": str(e)}
