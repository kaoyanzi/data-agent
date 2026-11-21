from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def merge_retrieved_info(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    try:
        writer({"type":"process","step":"合并召回信息","state":"running"})
        writer({"type":"process","step":"合并召回信息","state":"success"})
    except Exception as e:
        logger.error(str(e))
        writer({"type": "process", "step": "合并召回信息", "state": "failed"})
        raise e
