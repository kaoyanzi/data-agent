
from typing import Any

from sqlalchemy import text, Result
from sqlalchemy.ext.asyncio import AsyncSession


class DwMysqlRepository():
    """操作数据仓库mysql的持久层"""
    def __init__(self,session:AsyncSession):
        self.session = session

    async def get_column_type_by_table_id(self, table_id:str) -> dict[str,str]:
        sql = f"show columns from {table_id}"
        result:Result = await self.session.execute(text(sql))
        #多列多行结果
        return {row.Field:row.Type for row in result.fetchall()}

    async def get_column_values(self, table_id:str, column_name:str,limit:int=3)->list[str]:
        sql = f"select distinct {column_name} from {table_id} limit {limit}"
        result:Result = await self.session.execute(text(sql))
        #单列多行结果
        return result.scalars().fetchall()

    async def get_db_info(self)->dict[str,str]:
        """
        获取数仓数据库的方言和数据库的版本
        :return:
        """
        db_info:dict[str,str] = {}
        sql = "select version()"
        result:Result = await self.session.execute(text(sql))
        db_info["version"] = result.scalar()
        db_info["dialect"] = self.session.get_bind().dialect.name
        return db_info

    async def validate_sql(self, sql:str):
        """验证sql的合法性"""
        sql = f"explain {sql}"
        await self.session.execute(text(sql))

    async def excute_sql(self, sql:str)->list[dict[str,Any]]:
        result:Result = await self.session.execute(text(sql))
        #将结果每行记录转为字典:{字段名称/别名:字段取值} 多行记录[{},{}...]
        return [dict(row_mapping) for row_mapping in result.mappings().fetchall()]
