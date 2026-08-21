from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from ai.config import load_project_env
from ai.state import AgentState
from ai.retriever import get_retriever
from ai.text2sql import get_text2sql_engine
from pydantic import BaseModel, Field
from typing import Optional, List

ENV_PATH = load_project_env()

llm = init_chat_model("gpt-5.4-mini")

_retriever = None
_text2sql_engine = None


class VectorSearchQuery(BaseModel):
    """사이버보안 문서 검색을 위한 쿼리 분석 결과"""
    optimized_query: str = Field(
        description="CVE, CWE, CVSS, NIST 및 취약점 대응 문서 검색에 최적화된 쿼리"
    )
    categories: Optional[List[str]] = Field(
        default=None,
        description=(
            "선택된 보안 문서군 리스트(1-2개). 가능한 값: "
            "CVE Program, CWE, CVSS, Vulnerability Response, NIST. "
            "관련 문서군이 불명확하면 null"
        )
    )


def get_cached_retriever():
    """캐시된 retriever 인스턴스 반환 (lazy initialization)"""
    global _retriever
    if _retriever is None:
        _retriever = get_retriever()
    return _retriever


def get_cached_text2sql_engine():
    """캐시된 text2sql_engine 인스턴스 반환 (lazy initialization)"""
    global _text2sql_engine
    if _text2sql_engine is None:
        _text2sql_engine = get_text2sql_engine()
    return _text2sql_engine


def classify_intent(state: AgentState) -> AgentState:
    """
    사용자 질문의 의도를 분류하는 노드

    분류 결과:
    - 'general': 일반적인 대화나 인사
    - 'database': 데이터베이스 조회가 필요한 질문
    - 'vector': 문서 검색이 필요한 질문

    Args:
        state: 현재 상태

    Returns:
        업데이트된 상태
    """
    # messages에서 질문 추출
    messages = state.get("messages", [])
    if not messages:
        raise ValueError("No messages provided")

    # 마지막 사용자 메시지를 질문으로 사용
    question = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])

    system_prompt = """
당신은 CVE/CWE 기반 사이버보안 질의 라우팅 전문가입니다.

이전 대화 맥락을 고려하여 현재 질문을 다음 3가지 중 하나로 분류하세요:

1. 'general' - 인사, 감사, 시스템 사용법 또는 CVE/CWE 데이터·보안 문서와 무관한 일반 대화
   예: "안녕하세요", "고마워", "무슨 일을 할 수 있어?"

2. 'database' - Supabase의 "CVE", "CWE" 테이블에서 정확한 행, 목록, 통계 또는 비교를 조회해야 하는 질문
   - 특정 CVE/CWE ID, 공급업체, 제품, 취약점명, 등록일, 조치 기한, 랜섬웨어 연관 여부 조회
   - CWE 설명, 영향, 탐지 방법, 완화 방법 조회
   - 개수, 최근 순, 상위 유형, 그룹별 집계처럼 SQL이 필요한 질문
   예: "CVE-2024-43468의 대응 조치는?", "CWE-89 취약점 목록을 최근 순으로 보여줘", "랜섬웨어 연관 CVE가 많은 공급업체는?"

3. 'vector' - CVE/CWE/CVSS 표준, CNA 규칙, NIST 지침, 취약점 대응 절차 등 PDF 근거 문서 검색이 필요한 질문
   예: "CVE와 CWE의 차이는?", "CVSS v4 Attack Vector를 설명해줘", "CNA의 CVE 공개 원칙은?", "NIST 취약점 대응 절차는?"

분류 원칙:
- 질문에 CVE-연도-번호 또는 CWE-번호가 있고 해당 레코드의 속성을 요구하면 'database'
- 목록, 건수, 순위, 날짜, 공급업체, 제품, 랜섬웨어 여부를 요구하면 'database'
- 표준의 정의·원칙·평가 방법·대응 절차에 대한 근거 설명을 요구하면 'vector'
- CWE는 약점 유형이고 CVE는 개별 취약점 식별자이므로 서로 혼동하지 마세요

반드시 'general', 'database', 'vector' 중 하나만 답변하세요.
다른 설명 없이 분류 결과만 반환하세요.
"""

    # 시스템 메시지 + 전체 대화 히스토리
    conversation = [SystemMessage(content=system_prompt)] + messages

    response = llm.invoke(conversation)
    intent = response.content.strip().lower()

    # 유효한 의도인지 확인
    if intent not in ['general', 'database', 'vector']:
        intent = 'general'

    return {
        "intent": intent,
        "question": question
    }


def general_answer(state: AgentState) -> AgentState:
    """
    일반적인 질문에 직접 답변하는 노드

    Args:
        state: 현재 상태

    Returns:
        업데이트된 상태
    """
    # 대화 히스토리 가져오기
    messages = state.get("messages", [])

    system_prompt = """
당신은 CVE, CWE, CVSS와 취약점 대응을 다루는 친절한 사이버보안 AI 어시스턴트입니다.
사용자의 질문에 한국어로 자연스럽고 간결하게 답변하세요.
CVE는 개별 취약점 식별자, CWE는 약점 유형, CVSS는 심각도 평가 체계라는 차이를 유지하세요.
확인되지 않은 취약점 정보나 위험도를 추측하지 마세요.
"""

    # 시스템 메시지 + 기존 대화 히스토리
    conversation = [SystemMessage(content=system_prompt)] + messages

    response = llm.invoke(conversation)
    answer = response.content

    return {
        "messages": [AIMessage(content=answer)]
    }


def vector_search(state: AgentState) -> AgentState:
    """
    Qdrant 벡터 검색을 수행하는 노드

    1. LLM으로 질문 분석 (최적화된 쿼리 + 카테고리 추출)
    2. 병렬 벡터 검색 수행

    Args:
        state: 현재 상태

    Returns:
        업데이트된 상태
    """
    # 대화 히스토리 가져오기
    messages = state.get("messages", [])

    # 재작성된 쿼리가 있으면 사용, 없으면 원본 질문 사용
    original_query = state.get("rewritten_query") or state.get("question", "")

    # 이전 대화 맥락이 있으면 완전한 질문으로 재구성
    if len(messages) > 1 and not state.get("rewritten_query"):
        # rewritten_query가 없을 때만 (첫 시도) 맥락 고려
        system_prompt_complete = """
당신은 사이버보안 질문 분석 전문가입니다.
이전 대화 맥락을 고려하여 현재 질문을 완전하고 명확한 질문으로 재구성하세요.

예시:
- 이전: "CVSS v4의 Attack Vector를 설명해줘" → 현재: "Adjacent는 뭐야?" → 재구성: "CVSS v4 Attack Vector에서 Adjacent의 의미는 무엇인가?"
- 이전: "CNA의 CVE 공개 원칙은?" → 현재: "기한도 알려줘" → 재구성: "CNA가 CVE Record를 공개해야 하는 기한은 무엇인가?"

완전한 질문만 반환하세요. 설명은 포함하지 마세요.
만약 현재 질문이 이미 완전하다면 그대로 반환하세요.
"""
        conversation_complete = [SystemMessage(content=system_prompt_complete)] + messages
        response_complete = llm.invoke(conversation_complete)
        original_query = response_complete.content.strip()

    # 1. LLM으로 쿼리 분석 및 카테고리 추출 (Structured Output)
    # 시스템 프롬프트: 역할 정의 및 카테고리 설명
    system_prompt = """당신은 사이버보안 문서 검색 쿼리 최적화 전문가입니다.
사용자의 질문을 분석하여 CVE/CWE/CVSS/NIST 문서 검색에 적합한 핵심 쿼리를 생성하고, 관련 문서군을 선택하세요.

사용 가능한 문서군:
- CVE Program: CVE Record, CVE ID, CNA 역할·규칙·공개 및 분쟁 처리
- CWE: 소프트웨어/하드웨어 약점 분류, 관계, 원인, 영향 및 완화
- CVSS: 취약점 심각도 점수, 지표, 계산 및 해석
- Vulnerability Response: 취약점·사고 대응 플레이북, 우선순위와 운영 절차
- NIST: NIST 보안 지침과 표준

문서군 선택 규칙:
1. 명확하게 관련 있는 문서군만 1-2개 선택합니다
2. CVE, CWE, CVSS를 혼동하지 않습니다
3. 애매하거나 여러 문서군을 폭넓게 검색해야 하면 null을 반환합니다

출력 지침:
1. optimized_query: CVE/CWE 번호, 표준명, 영문 보안 용어와 핵심 개념을 보존한 검색 쿼리
2. categories: 관련 문서군 1-2개. 불확실하면 null"""

    # 유저 프롬프트: 실제 질문
    user_prompt = f"다음 질문을 분석해주세요:\n\n{original_query}"

    # 메시지 객체 생성 (Structured Output용)
    llm_messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    # Structured Output으로 LLM 호출
    structured_llm = llm.with_structured_output(VectorSearchQuery)
    query_analysis = structured_llm.invoke(llm_messages)

    optimized_query = query_analysis.optimized_query
    categories = query_analysis.categories

    print(f"[벡터 검색 쿼리 분석]")
    print(f"  원본 쿼리: {original_query}")
    print(f"  최적화된 쿼리: {optimized_query}")
    print(f"  선택된 카테고리: {categories}")

    # 2. 병렬 벡터 검색 수행 (카테고리 필터 적용)
    retriever = get_cached_retriever()
    results = retriever.search(optimized_query, k=3, score_threshold=0.5, categories=categories)

    return {
        "vector_results": results
    }


def rewrite_query(state: AgentState) -> AgentState:
    """
    검색 결과가 부족할 때 쿼리를 재작성하는 노드

    Args:
        state: 현재 상태

    Returns:
        업데이트된 상태
    """
    # 대화 히스토리 가져오기
    messages = state.get("messages", [])

    system_prompt = """
당신은 CVE/CWE/CVSS 보안 문서 검색 쿼리 최적화 전문가입니다.

사용자의 질문이 검색 결과를 얻지 못했습니다.
이전 대화 맥락을 고려하여 질문을 다시 작성하여 더 나은 검색 결과를 얻을 수 있도록 하세요.

최적화 방법:
- 이전 대화에서 언급된 맥락을 포함
- CVE/CWE 번호와 CVSS 버전은 원문 그대로 유지
- 한국어 보안 용어에 대응하는 영문 표준 용어 추가
- 동의어와 관련 공격·약점·대응 용어 추가
- 질문을 더 구체적이거나 더 일반적으로 변경
- 핵심 키워드 강조

재작성된 쿼리만 반환하세요. 설명은 포함하지 마세요.
"""

    # 시스템 메시지 + 전체 대화 히스토리
    conversation = [SystemMessage(content=system_prompt)] + messages

    response = llm.invoke(conversation)
    rewritten = response.content.strip()

    return {
        "rewritten_query": rewritten,
        "retry_count": state.get("retry_count", 0) + 1
    }


def database_query(state: AgentState) -> AgentState:
    """
    Text2SQL을 수행하여 데이터베이스를 조회하는 노드

    Args:
        state: 현재 상태

    Returns:
        업데이트된 상태
    """
    # 대화 히스토리 가져오기
    messages = state.get("messages", [])
    question = state.get("question", "")
    previous_error = state.get("error")

    # 이전 대화 맥락이 있으면 완전한 질문으로 재구성
    if len(messages) > 1:
        system_prompt = """
당신은 CVE/CWE 데이터 조회 질문 분석 전문가입니다.
이전 대화 맥락을 고려하여 현재 질문을 완전하고 명확한 질문으로 재구성하세요.

예시:
- 이전: "CVE-2024-43468 알려줘" → 현재: "조치 기한은?" → 재구성: "CVE-2024-43468의 조치 기한은?"
- 이전: "CWE-89 설명해줘" → 현재: "완화 방법은?" → 재구성: "CWE-89의 잠재적 완화 방법은?"
- 이전: "Microsoft 취약점 보여줘" → 현재: "랜섬웨어 관련된 것만" → 재구성: "Microsoft CVE 중 랜섬웨어 캠페인 사용이 Known인 취약점은?"

완전한 질문만 반환하세요. 설명은 포함하지 마세요.
만약 현재 질문이 이미 완전하다면 그대로 반환하세요.
"""
        conversation = [SystemMessage(content=system_prompt)] + messages
        response = llm.invoke(conversation)
        complete_question = response.content.strip()
    else:
        complete_question = question

    # Text2SQL 실행
    text2sql_engine = get_cached_text2sql_engine()
    result = text2sql_engine.query(complete_question, previous_error=previous_error)

    return {
        "sql_query": result["sql_query"],
        "db_results": result["result"],
        "error": result["error"],
        "retry_count": state.get("retry_count", 0) + 1
    }


def generate_answer(state: AgentState) -> AgentState:
    """
    검색 결과를 바탕으로 최종 답변을 생성하는 노드

    Args:
        state: 현재 상태

    Returns:
        업데이트된 상태
    """
    # 대화 히스토리 가져오기
    messages = state.get("messages", [])

    # 컨텍스트 구성
    context_parts = []

    # 벡터 검색 결과가 있으면 추가
    if state.get("vector_results"):
        docs = state["vector_results"]
        context_parts.append("관련 문서:")
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "알 수 없음")
            page = doc.metadata.get("page", "?")
            document_family = doc.metadata.get("document_family", "")

            # 출처 정보 구성
            source_info = f"출처: {source}, 페이지: {page}"
            if document_family:
                source_info += f", 문서군: {document_family}"

            context_parts.append(f"\n[문서 {i}] {source_info}\n{doc.page_content}")

    # DB 검색 결과가 있으면 추가
    if state.get("db_results"):
        context_parts.append(f"\n\nCVE/CWE 데이터베이스 조회 결과:\n{state['db_results']}")
        if state.get("sql_query"):
            context_parts.append(f"\n실행된 SQL:\n{state['sql_query']}")

    context = "\n".join(context_parts)

    system_prompt = f"""
당신은 CVE/CWE 데이터와 보안 표준 문서를 분석하는 사이버보안 전문가입니다.

다음 정보를 바탕으로 사용자의 질문에 정확하고 도움이 되는 답변을 제공하세요:

<context>
{context}
</context>

답변 시 다음 규칙을 따르세요:
- 주어진 검색 결과만 사실 근거로 사용하고 한국어로 질문에 먼저 직접 답하세요
- CVE는 개별 취약점, CWE는 약점 유형, CVSS는 심각도 평가 체계로 구분하세요
- CVE ID, CWE ID, 공급업체, 제품, 등록일, 조치 기한과 대응 조치를 정확히 표시하세요
- "knownRansomwareCampaignUse"가 Known일 때만 랜섬웨어 캠페인 연관이 확인됐다고 표현하세요
- 테이블에 CVSS 점수가 없으므로 별도 근거 없이 위험도나 심각도 순위를 만들지 마세요
- CVE 대응은 "requiredAction", CWE 완화는 "Potential Mitigations"를 우선 근거로 사용하세요
- 문서 근거에는 가능한 경우 파일명과 페이지를 함께 표시하세요
- 정보가 정말로 없는 경우에만 "해당 정보를 찾을 수 없습니다"라고 말하세요
- 이전 대화 맥락을 고려하여 답변하세요
"""

    # 시스템 메시지 + 기존 대화 히스토리
    conversation = [SystemMessage(content=system_prompt)] + messages

    response = llm.invoke(conversation)
    answer = response.content

    return {
        "messages": [AIMessage(content=answer)]
    }


def route_by_intent(state: AgentState) -> str:
    """
    의도에 따라 다음 노드를 결정하는 라우팅 함수

    Args:
        state: 현재 상태

    Returns:
        다음 노드 이름
    """
    intent = state.get("intent", "general")

    if intent == "general":
        return "general_security_answer"
    elif intent == "database":
        return "cve_cwe_database_query"
    elif intent == "vector":
        return "security_document_search"
    else:
        return "general_security_answer"


def check_vector_results(state: AgentState) -> str:
    """
    벡터 검색 결과를 확인하고 다음 노드를 결정하는 함수

    Args:
        state: 현재 상태

    Returns:
        다음 노드 이름
    """
    results = state.get("vector_results", [])
    retry_count = state.get("retry_count", 0)

    # 결과가 있거나 재시도 횟수가 2회 이상이면 답변 생성
    retriever = get_cached_retriever()
    if retriever.is_relevant(results) or retry_count >= 2:
        return "generate_security_answer"
    else:
        return "rewrite_security_query"


def check_db_results(state: AgentState) -> str:
    """
    데이터베이스 검색 결과를 확인하고 다음 노드를 결정하는 함수

    Args:
        state: 현재 상태

    Returns:
        다음 노드 이름
    """
    error = state.get("error")
    result = state.get("db_results")
    retry_count = state.get("retry_count", 0)

    # 오류가 없고 결과가 있으면 답변 생성
    text2sql_engine = get_cached_text2sql_engine()
    if not error and result and not text2sql_engine.is_empty_result(result):
        return "generate_security_answer"

    # 재시도 횟수가 2회 이상이면 답변 생성 (오류 메시지 포함)
    if retry_count >= 2:
        return "generate_security_answer"

    # 재시도
    return "cve_cwe_database_query"
