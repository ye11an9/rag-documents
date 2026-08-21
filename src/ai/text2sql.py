"""Supabase의 CVE/CWE 테이블을 위한 읽기 전용 Text2SQL 엔진."""

import os
import re

from ai.config import load_project_env
from langchain.chat_models import init_chat_model
from langchain_community.utilities import SQLDatabase
from langchain_core.messages import HumanMessage, SystemMessage


READ_ONLY_START_PATTERN = re.compile(r"^\s*(SELECT|WITH)\b", re.IGNORECASE)
FORBIDDEN_SQL_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|UPSERT|MERGE|DROP|ALTER|TRUNCATE|CREATE|"
    r"GRANT|REVOKE|COPY|CALL|DO|VACUUM|ANALYZE|COMMENT|REFRESH)\b",
    re.IGNORECASE,
)
SQL_LITERAL_OR_COMMENT_PATTERN = re.compile(
    r"'(?:''|[^'])*'|--[^\r\n]*|/\*.*?\*/",
    re.DOTALL,
)


class Text2SQLEngine:
    def __init__(self):
        """CVE/CWE 테이블만 노출하여 Text2SQL 엔진을 초기화한다."""
        load_project_env()
        database_url = os.getenv("SUPABASE_DB_URL")
        if not database_url:
            raise ValueError(".env에 SUPABASE_DB_URL을 설정해야 합니다.")

        self.db = SQLDatabase.from_uri(
            database_url,
            include_tables=["CVE", "CWE"],
            sample_rows_in_table_info=0,
        )
        self.llm = init_chat_model("gpt-5.4-mini")
        self.schema_info = self.db.get_table_info()

    @staticmethod
    def _clean_sql_response(response_text: str) -> str:
        """LLM 응답에서 Markdown fence와 SQLQuery 접두어만 제거한다."""
        sql_query = response_text.strip()
        fenced = re.search(
            r"```(?:sql)?\s*(.*?)\s*```",
            sql_query,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if fenced:
            sql_query = fenced.group(1).strip()

        sql_query = re.sub(
            r"^\s*(?:SQLQuery|SQL 쿼리|Query)\s*:\s*",
            "",
            sql_query,
            flags=re.IGNORECASE,
        )
        return sql_query.strip()

    @staticmethod
    def _validate_read_only_sql(sql_query: str) -> None:
        """데이터를 변경할 수 있는 SQL과 다중 문장을 실행 전에 차단한다."""
        if not sql_query or not READ_ONLY_START_PATTERN.match(sql_query):
            raise ValueError("SELECT 또는 WITH로 시작하는 조회 쿼리만 실행할 수 있습니다.")

        # 문자열 값 속의 'update', 세미콜론 등을 SQL 제어문으로 오인하지 않는다.
        control_text = SQL_LITERAL_OR_COMMENT_PATTERN.sub(" ", sql_query)
        control_text_without_final_semicolon = control_text.strip().rstrip(";").strip()
        if ";" in control_text_without_final_semicolon:
            raise ValueError("한 번에 하나의 SQL 문장만 실행할 수 있습니다.")

        if FORBIDDEN_SQL_PATTERN.search(control_text_without_final_semicolon):
            raise ValueError("데이터를 변경하거나 스키마를 조작하는 SQL은 실행할 수 없습니다.")

    def generate_sql(self, question: str, feedback: str = None) -> str:
        """자연어 질문을 PostgreSQL 조회 쿼리로 변환한다."""
        system_prompt = f"""
당신은 Supabase PostgreSQL의 CVE/CWE 데이터 조회 전문가입니다.
사용자의 질문을 아래 두 테이블만 사용하는 정확한 읽기 전용 SQL로 변환하세요.

<database_schema>
{self.schema_info}
</database_schema>

<table_descriptions>
1. "CVE": 실제로 공개·활용 우선순위가 정리된 개별 취약점 레코드
   - "cveID": CVE 식별자. 예: CVE-2024-43468
   - "vendorProject": 공급업체/프로젝트
   - "product": 영향받는 제품
   - "vulnerabilityName": 취약점명
   - "dateAdded": 데이터셋 등록일(YYYY-MM-DD 형식의 TEXT)
   - "shortDescription": 취약점 요약
   - "requiredAction": 권고되는 필수 대응 조치
   - "dueDate": 조치 기한(YYYY-MM-DD 형식의 TEXT)
   - "knownRansomwareCampaignUse": 알려진 랜섬웨어 캠페인 악용 여부
   - "notes": 참고 정보와 외부 링크
   - "cwes": 연결된 CWE 식별자 문자열. 예: CWE-89 또는 쉼표로 구분된 여러 값

2. "CWE": 소프트웨어·하드웨어 약점 유형의 상세 분류
   - "CWE-ID": 숫자형 CWE 번호. 예: CWE-89는 값 89로 조회
   - "Name", "Weakness Abstraction", "Status", "Description", "Extended Description"
   - "Related Weaknesses", "Weakness Ordinalities", "Applicable Platforms"
   - "Background Details", "Alternate Terms", "Modes Of Introduction"
   - "Exploitation Factors", "Likelihood of Exploit", "Common Consequences"
   - "Detection Methods", "Potential Mitigations", "Observed Examples"
   - "Functional Areas", "Affected Resources", "Taxonomy Mappings"
   - "Related Attack Patterns", "Notes"
</table_descriptions>

<rules>
- PostgreSQL 문법을 사용하고 SELECT 또는 읽기 전용 WITH 쿼리 하나만 생성하세요
- 대소문자와 공백/하이픈이 보존된 테이블·컬럼이므로 모든 식별자를 위 표기 그대로 큰따옴표로 감싸세요
- "CVE"와 "CWE" 외의 테이블이나 존재하지 않는 컬럼을 사용하지 마세요
- 특정 CVE ID는 "cveID", 특정 CWE-89는 "CWE-ID" = 89로 조회하세요
- CVE와 CWE를 연결할 때 다음 조건을 사용하세요:
  'CWE-' || w."CWE-ID"::text = ANY(regexp_split_to_array(c."cwes", E'\\\\s*,\\\\s*'))
- 공급업체, 제품, 취약점명 등 사용자 입력 문자열은 대소문자를 구분하지 않도록 ILIKE와 % 검색을 사용하세요
- 날짜 계산이나 정렬이 필요하면 NULLIF("dateAdded", '')::date 또는 NULLIF("dueDate", '')::date를 사용하세요
- 랜섬웨어 악용 확인 질문은 "knownRansomwareCampaignUse" 값을 조회·필터링하고 임의로 추정하지 마세요
- 상세 행이나 목록에는 필요한 컬럼만 선택하고 최대 20개로 LIMIT 하세요
- NULL과 빈 문자열을 구분하여 처리하세요
- SQL만 반환하세요. 설명, Markdown 코드 블록, SQLQuery 접두어는 포함하지 마세요
- 쿼리 끝에는 세미콜론 하나만 사용하세요
</rules>
"""

        if feedback:
            system_prompt += (
                "\n<previous_error>\n"
                f"{feedback}\n"
                "</previous_error>\n"
                "이 오류의 원인을 수정하되 위 스키마와 읽기 전용 규칙을 계속 지키세요."
            )

        response = self.llm.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=question)]
        )
        return self._clean_sql_response(response.content)

    def execute_sql(self, sql_query: str) -> tuple[str | None, str | None]:
        """검증된 단일 읽기 전용 SQL 쿼리를 실행한다."""
        try:
            self._validate_read_only_sql(sql_query)
            result = self.db.run(sql_query)
            return result, None
        except Exception as exc:
            return None, str(exc)

    def query(self, question: str, previous_error: str = None) -> dict:
        """SQL 생성과 실행 결과를 하나의 딕셔너리로 반환한다."""
        sql_query = self.generate_sql(question, feedback=previous_error)
        result, error = self.execute_sql(sql_query)
        return {"sql_query": sql_query, "result": result, "error": error}

    @staticmethod
    def is_empty_result(result: str | None) -> bool:
        """SQLDatabase 문자열 결과가 비어 있는지 확인한다."""
        if not result:
            return True

        empty_patterns = ["[]", "()", "no rows", "0 rows"]
        result_lower = result.lower().strip()
        return any(pattern in result_lower for pattern in empty_patterns)


def get_text2sql_engine() -> Text2SQLEngine:
    """Text2SQL 엔진 인스턴스를 반환한다."""
    return Text2SQLEngine()
