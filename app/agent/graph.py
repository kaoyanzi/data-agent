import asyncio

from langgraph.constants import START,END
from langgraph.graph import StateGraph

from app.agent.context import DataAgentContext
from app.agent.nodes.add_extra_context import add_extra_context
from app.agent.nodes.correct_sql import correct_sql
from app.agent.nodes.execute_sql import execute_sql
from app.agent.nodes.extract_keywords import extract_keywords
from app.agent.nodes.filter_metric import filter_metric
from app.agent.nodes.filter_table import filter_table
from app.agent.nodes.generate_sql import generate_sql
from app.agent.nodes.merge_retrieved_info import merge_retrieved_info
from app.agent.nodes.recall_column import recall_column
from app.agent.nodes.recall_metric import recall_metric
from app.agent.nodes.recall_value import recall_value
from app.agent.nodes.validate_sql import validate_sql
from app.agent.state import DataAgentState
from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import dw_mysql_client_manager, meta_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.repositories.es.value_es_repository import ValueInfoRepository
from app.repositories.mysql.dw_mysql_repository import DwMysqlRepository
from app.repositories.mysql.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repositoty import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository

graph_bulider = StateGraph(
    state_schema=DataAgentState,
    context_schema=DataAgentContext,
)

graph_bulider.add_node("extract_keywords",extract_keywords)
graph_bulider.add_node("recall_column",recall_column)
graph_bulider.add_node("recall_metric",recall_metric)
graph_bulider.add_node("recall_value",recall_value)
graph_bulider.add_node("merge_retrieved_info",merge_retrieved_info)
graph_bulider.add_node("filter_table",filter_table)
graph_bulider.add_node("filter_metric",filter_metric)
graph_bulider.add_node("add_extra_context",add_extra_context)
graph_bulider.add_node("generate_sql",generate_sql)
graph_bulider.add_node("validate_sql",validate_sql)
graph_bulider.add_node("correct_sql",correct_sql)
graph_bulider.add_node("execute_sql",execute_sql)

graph_bulider.add_edge(START,"extract_keywords")
graph_bulider.add_edge("extract_keywords","recall_column")
graph_bulider.add_edge("extract_keywords","recall_metric")
graph_bulider.add_edge("extract_keywords","recall_value")

graph_bulider.add_edge("recall_column","merge_retrieved_info")
graph_bulider.add_edge("recall_metric","merge_retrieved_info")
graph_bulider.add_edge("recall_value","merge_retrieved_info")


graph_bulider.add_edge("merge_retrieved_info","filter_table")
graph_bulider.add_edge("merge_retrieved_info","filter_metric")

graph_bulider.add_edge("filter_table","add_extra_context")
graph_bulider.add_edge("filter_metric","add_extra_context")


graph_bulider.add_edge("add_extra_context","generate_sql")
graph_bulider.add_edge("generate_sql","validate_sql")

#新增条件边,state中的error error有值则去修复SQL节点,反之去执行SQL节点
graph_bulider.add_conditional_edges("validate_sql",lambda state:"execute_sql" if state['error'] is None else "correct_sql",path_map={"execute_sql":"execute_sql","correct_sql":"correct_sql"})
graph_bulider.add_edge("correct_sql","validate_sql")
graph_bulider.add_edge("execute_sql",END)

graph = graph_bulider.compile()

if __name__ == '__main__':
    # print(graph.get_graph().draw_mermaid())

    # state = DataAgentState(query="统计华北地区的销售额")
    # result = graph.invoke(input=state)
    # print(result)

    async def test_graph():
        state = DataAgentState(query="2025 年 1 月各省份订单金额排名")

        dw_mysql_client_manager.init()
        meta_mysql_client_manager.init()
        embedding_client_manager.init()
        es_client_manager.init()
        qdrant_client_manager.init()

        async with dw_mysql_client_manager.session_factory() as dw_session,meta_mysql_client_manager.session_factory() as meta_session:

            context = DataAgentContext(
                dw_mysql_repository=DwMysqlRepository(dw_session),
                meta_mysql_repository=MetaMysqlRepository(meta_session),
                embedding_client=embedding_client_manager.embedding_client,
                value_info_repository=ValueInfoRepository(es_client_manager.client),
                column_qdrant_repository=ColumnQdrantRepository(qdrant_client_manager.client),
                metric_qdrant_repository=MetricQdrantRepository(qdrant_client_manager.client),
            )
            #无论是invoke还是ainvoke都是一次性将state返回
            # result = await graph.ainvoke(input=state,context=context)
            # print(result)
            #采用流式调用 流模式默认是updates  values:每个步骤输出完成的state  updates:每个步骤输出更新的部分   custom:自定义输出

            async for chunk in graph.astream(input=state,context=context,stream_mode="custom"):
                print(chunk)

        await dw_mysql_client_manager.close()
        await meta_mysql_client_manager.close()
        await es_client_manager.close()
        await qdrant_client_manager.close()


    asyncio.run(test_graph())