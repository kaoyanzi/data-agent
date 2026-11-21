from datetime import datetime

from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState, DateInfoState, DBInfoState
from app.core.log import logger


async def add_extra_context(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    try:
        writer({"type":"process","step":"添加额外的上下文","state":"running"})
        # 1.获取当前时间 日期、星期、季度
        today = datetime.today()
        # 日期
        date = today.strftime("%Y-%m-%d")
        # 星期
        weekday = today.strftime("%A")
        # 季度
        quarter = f"Q{(today.month - 1) // 3 + 1}"
        date_info = DateInfoState(
            date=date,
            weekday=weekday,
            quarter=quarter
        )
        logger.info("新增额外的上下文日期信息:{}",date_info)
        dw_mysql_repository= runtime.context["dw_mysql_repository"]
        db_indo_dict:dict[str,str] = await dw_mysql_repository.get_db_info()
        db_info = DBInfoState(
            dialect=db_indo_dict["dialect"],
            version=db_indo_dict["version"],
        )
        logger.info("额外的上下文的数据库的信息:{}",db_info)
        writer({"type":"process","step":"添加额外的上下文","state":"success"})
        return {"date_info": date_info, "db_info": db_info}
    except Exception as e:
        logger.error(str(e))
        writer({"type": "process", "step": "添加额外的上下文", "state": "failed"})
        raise e
