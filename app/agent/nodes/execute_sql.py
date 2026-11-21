from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def execute_sql(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    try:
        writer({"type":"process","step":"执行SQL","state":"running"})

        writer({"type":"process","step":"执行SQL","state":"success"})

        writer({"type":"result","data":None})
    except Exception as e:
        logger.error(str(e))
        writer({"type": "process", "step": "执行SQL", "state": "failed"})
        raise e
