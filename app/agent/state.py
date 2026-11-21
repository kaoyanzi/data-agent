from typing import TypedDict

from app.entities.column_info import ColumnInfo
from app.entities.metric_info import MetricInfo
from app.entities.value_info import ValueInfo


class DataAgentState(TypedDict):
    """状态"""
    query:str   #用户的问题
    keywords:list[str]  #抽取关键词产生的关键词列表
    retrieved_columns: list[ColumnInfo]  # 召回列信息列表
    retrieved_metrics: list[MetricInfo]     #召回指标节点产生的结果
    retrieved_values: list[ValueInfo]   #召回字段取值
    error:str #检验SQL节点用于存放错误信息