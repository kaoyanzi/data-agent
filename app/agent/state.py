from typing import TypedDict

from app.entities.column_info import ColumnInfo
from app.entities.metric_info import MetricInfo
from app.entities.value_info import ValueInfo

class ColumnInfoState(TypedDict):
    name: str
    type: str
    role: str
    examples: list
    description: str
    alias: list[str]

# 表信息封装实体
class TableInfoStata(TypedDict):
    name: str
    role: str
    description: str
    columns: list[ColumnInfoState]

# 指标信息封装实体
class MetricInfoStata(TypedDict):
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]


class DateInfoState(TypedDict):
    date: str
    weekday: str
    quarter: str


class DBInfoState(TypedDict):
    version: str
    dialect: str

class DataAgentState(TypedDict):
    """状态"""
    query:str   #用户的问题
    keywords:list[str]  #抽取关键词产生的关键词列表
    retrieved_columns: list[ColumnInfo]  # 召回列信息列表
    retrieved_metrics: list[MetricInfo]     #召回指标节点产生的结果
    retrieved_values: list[ValueInfo]   #召回字段取值

    table_infos: list[TableInfoStata]
    metric_infos: list[MetricInfoStata]

    """
        图的状态定义
        存储的数据：graph运行需要依赖和处理的数据
       """
    date_info: DateInfoState
    db_info: DBInfoState

    sql:str #生成sql节点产生的纯文本的sql

    error:str #检验SQL节点用于存放错误信息

    modify_count:int    #记录修改sql的次数

