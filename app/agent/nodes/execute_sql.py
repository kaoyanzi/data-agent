from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def execute_sql(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    try:
        writer({"type":"process","step":"执行SQL","state":"running"})
        sql = state["sql"]
        dw_mysql_repository = runtime.context["dw_mysql_repository"]
        data = await dw_mysql_repository.excute_sql(sql)
        writer({"type":"process","step":"执行SQL","state":"success"})
        logger.info("SQL的执行结果:{}",data)
        writer({"type":"result","data":data})
    except Exception as e:
        logger.error(str(e))
        writer({"type": "process", "step": "执行SQL", "state": "failed"})
        raise e
