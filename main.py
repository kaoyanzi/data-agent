import time
import uuid
from urllib.request import Request

import uvicorn
from fastapi import FastAPI

from app.api.routers.hello_router import hello_router
from app.api.routers.query_router import query_router
from app.core.context import request_id_ctx_var
from app.core.lifespan import lifespan

app = FastAPI(lifespan=lifespan)

#引入自定义的路由
app.include_router(hello_router)
app.include_router(query_router)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    为每次请求新增处理逻辑
    :param request: 请求对象
    :param call_next: 调用路由处理函数
    :return: 响应对象
    """
    # 记录请求处理开始时间（使用高精度计时器）
    start_time = time.perf_counter()
    #为本次请求服务端产生的协程对象设置请求id
    request_id_ctx_var.set(str(uuid.uuid4()))
    # 调用后续的请求处理逻辑（路由函数/其他中间件），获取响应对象
    response = await call_next(request)
    # 计算请求处理总耗时（结束时间 - 开始时间）
    process_time = time.perf_counter() - start_time
    # 将处理耗时添加到响应头中，键为X-Process-Time，值为耗时字符串
    response.headers["X-Process-Time"] = str(process_time)
    # 返回处理后的响应对象
    return response


if __name__ == '__main__':
    """
    命令行启动:1.fastapi dev 2.uv run python -m main
    Pycharm工具新建运行配置: 注意:如果要断点调试要去掉--reload参数
    """
    uvicorn.run(app="main:app", reload=True)
