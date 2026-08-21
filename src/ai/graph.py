"""CVE/CWE 데이터와 보안 문서를 함께 조회하는 LangGraph 워크플로."""

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
    """질문을 CVE/CWE DB 또는 보안 문서 검색 경로로 라우팅한다."""
    # StateGraph 생성 (input state 명시)
    graph_builder = StateGraph(AgentState, input=InputState)

    # LangGraph Studio에서도 각 노드의 보안 도메인 역할이 드러나도록 이름을 지정한다.
    graph_builder.add_node("security_intent_classifier", classify_intent)
    graph_builder.add_node("general_security_answer", general_answer)
    graph_builder.add_node("security_document_search", vector_search)
    graph_builder.add_node("cve_cwe_database_query", database_query)
    graph_builder.add_node("rewrite_security_query", rewrite_query)
    graph_builder.add_node("generate_security_answer", generate_answer)

    # 시작점 설정
    graph_builder.set_entry_point("security_intent_classifier")

    # 의도별 조건부 라우팅
    graph_builder.add_conditional_edges(
        "security_intent_classifier",
        route_by_intent,
        {
            "general_security_answer": "general_security_answer",
            "cve_cwe_database_query": "cve_cwe_database_query",
            "security_document_search": "security_document_search",
        }
    )

    # 일반 답변은 바로 종료
    graph_builder.add_edge("general_security_answer", END)

    # 벡터 검색 후 결과 확인
    graph_builder.add_conditional_edges(
        "security_document_search",
        check_vector_results,
        {
            "generate_security_answer": "generate_security_answer",
            "rewrite_security_query": "rewrite_security_query",
        }
    )

    # 쿼리 재작성 후 다시 벡터 검색
    graph_builder.add_edge("rewrite_security_query", "security_document_search")

    # DB 검색 후 결과 확인
    graph_builder.add_conditional_edges(
        "cve_cwe_database_query",
        check_db_results,
        {
            "generate_security_answer": "generate_security_answer",
            "cve_cwe_database_query": "cve_cwe_database_query",  # 재시도
        }
    )

    # 최종 답변 후 종료
    graph_builder.add_edge("generate_security_answer", END)

    # 그래프 컴파일
    graph = graph_builder.compile()

    return graph


# 그래프 인스턴스 생성 (LangGraph Studio에서 사용)
graph = create_graph()
