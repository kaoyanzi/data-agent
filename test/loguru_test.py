import sys

from loguru import logger


logger.remove()

# 配置日志格式
log_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    # "<magenta>request_id - {extra[request_id]}</magenta> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

logger.add(sink=sys.stdout,level="INFO",format=log_format)
logger.add(
        sink="app.log",
        level="WARNING",
        format=log_format,
        rotation="128kb",
        retention="7 days",
        encoding="utf-8"
    )
logger.debug("xx")
logger.info("xx")
logger.warning("xx")
logger.error("xx")