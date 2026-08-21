from typing import Optional
from langgraph.graph import MessagesState


class InputState(MessagesState): # messagesState를 상속받아 InputState 정의
    pass


class AgentState(MessagesState):
    # 사용자 질문 및 의도
    question: Optional[str] # 사용자의 원본 질문
    intent: Optional[str] # 질문 의도 분류 결과 ('general', 'vector', 'database')

    # 벡터 검색 관련
    vector_results: Optional[list] # Qdrant 벡터 검색 결과 (Document 리스트)
    rewritten_query: Optional[str] # 재작성된 검색 쿼리 (벡터 검색용)

    # 데이터베이스 검색 관련
    sql_query: Optional[str] # 생성된 SQL 쿼리
    db_results: Optional[str] # 데이터베이스 쿼리 실행 결과

    # 오류 처리
    retry_count: Optional[int] # 재시도 횟수 (기본값 0)
    error: Optional[str] # 오류 메시지
