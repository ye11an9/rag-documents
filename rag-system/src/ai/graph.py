from langgraph.graph import StateGraph, END
from ai.state import AgentState, InputState
from ai.nodes import (
    classify_intent,
    general_answer,
    vector_search,
    database_query,
    rewrite_query,
    generate_answer,
    route_by_intent,
    check_vector_results,
    check_db_results,
)


def create_graph():
    # StateGraph 생성 (input state 명시)
    graph_builder = StateGraph(AgentState, input=InputState)

    # 노드 추가
    graph_builder.add_node("classify_intent", classify_intent)
    graph_builder.add_node("general_answer", general_answer)
    graph_builder.add_node("vector_search", vector_search)
    graph_builder.add_node("database_query", database_query)
    graph_builder.add_node("rewrite_query", rewrite_query)
    graph_builder.add_node("generate_answer", generate_answer)

    # 시작점 설정
    graph_builder.set_entry_point("classify_intent")

    # 의도별 조건부 라우팅
    graph_builder.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "general_answer": "general_answer",
            "database_query": "database_query",
            "vector_search": "vector_search",
        }
    )

    # 일반 답변은 바로 종료
    graph_builder.add_edge("general_answer", END)

    # 벡터 검색 후 결과 확인
    graph_builder.add_conditional_edges(
        "vector_search",
        check_vector_results,
        {
            "generate_answer": "generate_answer",
            "rewrite_query": "rewrite_query",
        }
    )

    # 쿼리 재작성 후 다시 벡터 검색
    graph_builder.add_edge("rewrite_query", "vector_search")

    # DB 검색 후 결과 확인
    graph_builder.add_conditional_edges(
        "database_query",
        check_db_results,
        {
            "generate_answer": "generate_answer",
            "database_query": "database_query",  # 재시도
        }
    )

    # 최종 답변 후 종료
    graph_builder.add_edge("generate_answer", END)

    # 그래프 컴파일
    graph = graph_builder.compile()

    return graph


# 그래프 인스턴스 생성 (LangGraph Studio에서 사용)
graph = create_graph()
