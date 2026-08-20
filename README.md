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

## 두 가지 구현 버전

이 저장소에는 서로 독립적인 두 구현이 공존합니다. (둘 다 `rag-system/examples/`)

| 버전 | 파일 | 특징 |
|---|---|---|
| 팀 완성본 | `rag-system/examples/day2_team_project_template.ipynb` | PDF 자동 선별, 결정적 ID 멱등 저장, 로컬 해시 임베딩 폴백 |
| 하이브리드 버전 | `rag-system/examples/day2_hybrid_rag.ipynb` | 하이브리드 검색(BM25+RRF), 카테고리 필터, 이식용 셀 제공 |

## 하이브리드 버전: `rag-system/examples/day2_hybrid_rag.ipynb`

Parent Document RAG를 Jupyter 노트북으로 구현한 버전으로, 다음 기능이 적용되어 있습니다.

1. **청킹** — chunk_size 900 / chunk_overlap 150 (팀 합의값, 노트북 상단 `CHUNK_SIZE`/`CHUNK_OVERLAP`으로 조정)
2. **검색 개수** — Parent retriever k=4, child 후보는 k×3 검색 후 중복 제거
3. **프롬프트** — "핵심 답변 / 상세 설명(표) / 출처" 3단 답변 형식 강제
4. **메타데이터 필터** — 문서별 `category` 부여 (CVE 관리, 취약점 평가, 사고 대응, SCAP 표준, 취약점 공개, CVE 작성 가이드) 및 Qdrant payload 인덱스 기반 필터 검색
5. **하이브리드 검색** — BM25(rank-bm25) + 벡터 검색을 RRF(Reciprocal Rank Fusion)로 융합. BM25 토크나이저는 kiwipiepy 형태소 분석(조사·어미 제거)을 사용하며, 미설치 시 정규식+불용어로 폴백

### 팀원 이식용 셀

노트북 안의 `[이식용]` 표시 셀 3개는 다른 노트북에 **그 셀만 복사해도 동작**하도록 작성되어 있습니다. 각 셀 상단 주석에 전제 변수·변수명 매핑이 명시되어 있습니다.

- **[이식용 A]** 카테고리 메타데이터 부여 + Qdrant payload 필터 (요구: `docs`)
- **[이식용 B]** BM25 인덱스 + 벡터 RRF 하이브리드 (요구: `child_docs`, `vectorstore`, `parent_docstore`)
- **[이식용 C]** Parent retriever k 튜닝 (요구: `vectorstore`, `parent_docstore`)

PDF 경로는 노트북 상단 `PDF_DIR` 변수 하나로 관리합니다 (기본값 `rag-system/datasets/보안 pdf모음/`, 대안 예: `../datasets/보안 취약점 PDF`).
