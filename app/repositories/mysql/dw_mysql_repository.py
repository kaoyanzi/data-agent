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
