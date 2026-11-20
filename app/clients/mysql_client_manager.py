import asyncio
from typing import Optional, Union

from sqlalchemy import text, Result
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession, async_sessionmaker

from app.conf.app_config import DBConfig, app_config
from app.models.table_info_mysql import TableInfoMySQL


class MySQLClientManager:
    """
    创建不用数据库操作需要的引擎对象engine,会话工厂session_factory用于产生Session
    """


    def __init__(self,db_config:DBConfig):
        self.db_config = db_config
        #self.engine:AsyncEngine|None = None
        #self.engine:Optional[AsyncEngine] = None
        self.engine:Union[AsyncEngine,None] = None
        self.session_factory:async_sessionmaker[AsyncSession]|None = None


    def _get_url(self):
        return f"mysql+asyncmy://{self.db_config.user}:{self.db_config.password}@{self.db_config.host}:{self.db_config.port}/{self.db_config.database}?charset=utf8mb4"
    def init(self):
        """为引擎对象赋值create_async_engine(url:数据库连接字符串,echo=是否控制台输出生成的sql)"""
        self.engine = create_async_engine(url=self._get_url(),echo=False)
        #autobegin控制事务是否自动开启
        self.session_factory = async_sessionmaker(bind=self.engine,autobegin=True,autoflush=True,expire_on_commit=False)

    async def close(self):
        if self.engine:
            await self.engine.dispose()
#对外暴露操作dw库管理对象
dw_mysql_client_manager = MySQLClientManager(db_config=app_config.db_dw)
meta_mysql_client_manager = MySQLClientManager(db_config=app_config.db_meta)

if __name__ == "__main__":
    dw_mysql_client_manager.init()
    meta_mysql_client_manager.init()
    async def test_dw():
        """用于测试dw库crud操作"""
        async with AsyncSession(dw_mysql_client_manager.engine) as dw_session:
            #1.执行自定义的sql,必须用text方法转化为TextClause类型
            result:Result = await dw_session.execute(text("SELECT MD5('abc')"))
            #2.结果单列单行scalar()或者scalar_one()获取结果
            print(result.scalar())
        #关闭资源
        await dw_mysql_client_manager.close()


    async def test_session_factory():
        async with meta_mysql_client_manager.session_factory() as meta_session:
            #1.新增表信息记录
            table_info_mysql = TableInfoMySQL(
                id="fact_payment3",
                name="fact_payment3",
                description="支付信息表3",
                role="fact",
            )
            meta_session.add(table_info_mysql)
            #目前事务未提交    autoflush = True 当前会话内可以获得未提交的数据

            # CRUD执行后手动提交事务
            await meta_session.commit()

            # 获取内存中的对象table_info_mysql  expire_on_commit=False 从内存中获取 ORM 对象相关信息    优点:提升性能  缺点:可能会返回脏数据
            # expire_on_commit = True 对象过期 再次获取就会报错 解决方案await meta_session.refresh(table_info_mysql) 再次发出一条查询SQL获取最新结果  优点缺点上面相反
            await meta_session.refresh(table_info_mysql)
            print(table_info_mysql.description)

            #根据id查询
            result:TableInfoMySQL = await meta_session.get(TableInfoMySQL,'fact_payment')
            print(result.description)



        await meta_mysql_client_manager.close()
    async def test_sql():
        async with AsyncSession(dw_mysql_client_manager.engine) as dw_session:
            result:Result = await dw_session.execute(text("select * from fact_order"))
            #多行多列的结果获取 fetchall()返回的是一个元组列表,元组中的值是每列的取值
            #fetchmany(10)可以指定返回的记录行数       fetchone()返回的是第一条记录使用元组返回
            #mappings()先映射为字典列表[{},{}...]
            print(result.mappings().fetchall())

    asyncio.run(test_sql())
    #asyncio.run(test_session_factory())
