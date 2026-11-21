from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState, TableInfoStata, ColumnInfoState, MetricInfoStata
from app.core.log import logger
from app.entities.column_info import ColumnInfo
from app.entities.metric_info import MetricInfo
from app.entities.table_info import TableInfo
from app.entities.value_info import ValueInfo
from app.repositories.mysql.meta_mysql_repository import MetaMysqlRepository


async def merge_retrieved_info(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    try:
        writer({"type":"process","step":"合并召回信息","state":"running"})
        retrieved_columns:list[ColumnInfo] = state["retrieved_columns"]
        retrieved_columns_dict:dict[str,ColumnInfo] = {column.id:column  for column in retrieved_columns}

        meta_mysql_repository:MetaMysqlRepository = runtime.context["meta_mysql_repository"]
        retrieved_metrics:list[MetricInfo] = state["retrieved_metrics"]
        for retrieved_metric in retrieved_metrics:
            for column_id in retrieved_metric.relevant_columns:
                if column_id not in retrieved_columns_dict:
                    column_info:ColumnInfo = await meta_mysql_repository.get_column_info_by_id(column_id)
                    retrieved_columns_dict[column_id] = column_info

        retrieved_values:list[ValueInfo] = state["retrieved_values"]
        for value_info in retrieved_values:
            column_id = value_info.column_id
            if column_id not in retrieved_columns_dict:
                column_info: ColumnInfo = await meta_mysql_repository.get_column_info_by_id(column_id)
                retrieved_columns_dict[column_id] = column_info
            if value_info.value not in retrieved_columns_dict[column_id].examples:
                retrieved_columns_dict[column_id].examples.append(value_info.value)

        table_id_columns_dict:dict[str,list[ColumnInfo]] = {}
        for column_info in retrieved_columns_dict.values():
            table_id = column_info.table_id
            if table_id not in table_id_columns_dict:
                table_id_columns_dict[table_id] = []
            table_id_columns_dict[table_id].append(column_info)

        for table_id in table_id_columns_dict.keys():
            existing_column_ids = [column.id for column in table_id_columns_dict[table_id]]
            key_columns:list[ColumnInfo] = await meta_mysql_repository.get_key_columns(table_id)
            for key_column in key_columns:
                column_id = key_column.id
                if column_id not in existing_column_ids:
                    table_id_columns_dict[table_id].append(key_column)

        table_infos:list[TableInfoStata] = []
        for table_id,column_infos in table_id_columns_dict.items():
            table_info:TableInfo = await meta_mysql_repository.get_table_info_by_id(table_id)
            table_info_state = TableInfoStata(
                name=table_info.name,
                role=table_info.role,
                description=table_info.description,
                columns=[ColumnInfoState(
                    name=column.name,
                    type=column.type,
                    role=column.role,
                    examples=column.examples,
                    description=column.description,
                    alias=column.alias,
                ) for column in column_infos]
            )
            table_infos.append(table_info_state)
        logger.info("合并召回信息的节点:{}",table_infos)

        metric_infos:list[MetricInfoStata] = []
        for retrieved_metric in retrieved_metrics:
            metric_info = MetricInfoStata(
                name=retrieved_metric.name,
                description=retrieved_metric.description,
                relevant_columns=retrieved_metric.relevant_columns,
                alias=retrieved_metric.alias,
            )
            metric_infos.append(metric_info)
        logger.info("合并召回信息的节点:{}", metric_infos)

        writer({"type":"process","step":"合并召回信息","state":"success"})
        return {"table_infos":table_infos,"metric_infos":metric_infos}
    except Exception as e:
        logger.error(str(e))
        writer({"type": "process", "step": "合并召回信息", "state": "failed"})
        raise e
