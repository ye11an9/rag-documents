# 보안 취약점 문서 기반 RAG 시스템

## 팀 프로젝트 주제 및 데이터

### Day 2 — 보안 취약점 문서 기반 RAG

CVE, CWE, CVSS, NIST, OWASP 등 보안 표준과 취약점 대응 문서를 검색해 근거가 있는 답변을 생성하는 RAG 프로젝트입니다. `rag-system/datasets/`에 있는 보안 PDF를 페이지와 Child chunk로 나누어 Qdrant Cloud에 저장하며, 답변에 참고 파일과 페이지를 표시합니다.

- 실행 노트북: [`examples/day2_team_project_template.ipynb`](examples/day2_team_project_template.ipynb)
- 사용 데이터: CVE/CWE/CVSS 명세, NIST 지침, OWASP 자료, 취약점 공개·대응 관련 PDF

### Day 3 — CVE·CWE Text2SQL

자연어 보안 질문을 PostgreSQL 쿼리로 변환해 실제 악용 취약점과 취약점 유형을 분석하는 Text2SQL 프로젝트입니다. CISA KEV의 CVE 데이터와 MITRE CWE Comprehensive View 데이터를 Supabase의 `CVE`, `CWE` 테이블에 저장하고, 복수 CWE 값을 분해해 두 테이블을 연결합니다.

- 실행 노트북: [`examples/day3_team_project_template.ipynb`](examples/day3_team_project_template.ipynb)
- 사용 데이터: CISA Known Exploited Vulnerabilities의 `cve.csv`, MITRE CWE Comprehensive View의 `cwe.csv`

`datasets/`의 CVE, CWE, CVSS, NIST, OWASP 및 취약점 대응 PDF를 자동으로 골라 Qdrant Cloud에 인덱싱하고, 검색 근거의 파일명과 페이지를 표시하는 2일차 팀 프로젝트입니다. 천안시 정책 실습 PDF는 인덱싱 대상에서 명시적으로 제외합니다.

## 구현 흐름

1. 실행 위치와 환경 변수 검증
2. 보안 PDF 선별 및 페이지 단위 Parent 문서 생성
3. 검색용 Child chunk 생성
4. Qdrant Cloud에 결정적 ID로 멱등 저장
5. Child 검색 결과를 원본 Parent 페이지로 확장
6. 검색된 문서만 근거로 답변하고 파일명·페이지 표시

## 빠른 시작

Python 3.10 이상이 필요합니다.

```bash
cd rag-system
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e .
```

`.env.example`을 `.env`로 복사하고 Qdrant Cloud 접속 정보를 입력합니다.

```dotenv
QDRANT_URL=https://your-cluster-url.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key
OPENAI_API_KEY=your-openai-api-key
```

사용 권한이 있는 보안 PDF를 `rag-system/datasets/`에 직접 넣은 뒤 실행합니다.

Jupyter에서는 완성된 [`rag-system/examples/day2_team_project_template.ipynb`](rag-system/examples/day2_team_project_template.ipynb)를 열어 **Run All**로 실행할 수 있습니다.

프로젝트 루트의 `.env`는 절대경로로 찾아 `override=True`로 로드합니다. 따라서 Windows나 Jupyter 프로세스에 오래된 API 키가 남아 있어도 이 프로젝트의 설정을 우선합니다. OpenAI 키가 없거나 호출이 실패하면 결정적 로컬 해시 임베딩과 근거 발췌 답변으로 폴백하며, Qdrant Cloud 정보는 항상 필요합니다.

## 인덱싱 특성

- 파일명이 숫자/CWE 번호로 시작하거나 `CVE`, `CWE`, `CVSS`, `NIST`, `OWASP`, `vulnerability`, `취약점` 등의 힌트를 포함한 PDF만 선택합니다.
- `2026 달라지는 천안 새로운 변화.pdf`, `2026 주요업무계획.pdf`는 제외합니다.
- `_with_`, `_in_`, `_colored` 등 동일 CWE 도표의 시각화 파생본은 제외합니다.
- PDF 추출 텍스트의 과도한 공백과 빈 줄을 정규화합니다.
- PDF 내용, 청킹 설정, 임베딩 백엔드의 지문을 컬렉션명에 반영합니다.
- Parent/Child ID가 결정적이며, 재실행 시 이미 존재하는 Qdrant point는 다시 임베딩하지 않습니다.
- 벡터 검색 후보를 보안 용어와 정의 문장 일치도로 재정렬합니다.
- Parent 문서는 실행 중 메모리에 보관되므로 질문 전에 같은 PDF 집합으로 스크립트를 실행해야 합니다.

자세한 데이터 준비 방법은 [datasets/README.md](datasets/README.md)를 참고하세요.
