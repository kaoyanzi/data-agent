from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def add_extra_context(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    try:
        writer({"type":"process","step":"添加额外的上下文","state":"running"})
        writer({"type":"process","step":"添加额外的上下文","state":"success"})
    except Exception as e:
        logger.error(str(e))
        writer({"type": "process", "step": "添加额外的上下文", "state": "failed"})
        raise e
