# 보안 취약점 문서 기반 RAG 시스템

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

사용 권한이 있는 보안 PDF를 `datasets/`에 직접 넣은 뒤 실행합니다. PDF 자체는 이 저장소에 포함하지 않습니다.

```bash
python notebooks/day2_security_rag.py
```

VS Code나 Jupyter에서 셀 단위로 실행하려면 `# %%` 구분자를 지원하는 편집기에서 `notebooks/day2_security_rag.py`를 여세요. OpenAI 키가 없거나 호출이 실패하면 결정적 로컬 해시 임베딩과 근거 발췌 답변으로 폴백합니다. Qdrant Cloud 정보는 항상 필요합니다.

## 인덱싱 특성

- 파일명이 숫자/CWE 번호로 시작하거나 `CVE`, `CWE`, `CVSS`, `NIST`, `OWASP`, `vulnerability`, `취약점` 등의 힌트를 포함한 PDF만 선택합니다.
- `2026 달라지는 천안 새로운 변화.pdf`, `2026 주요업무계획.pdf`는 제외합니다.
- PDF 내용, 청킹 설정, 임베딩 백엔드의 지문을 컬렉션명에 반영합니다.
- Parent/Child ID가 결정적이며, 재실행 시 이미 존재하는 Qdrant point는 다시 임베딩하지 않습니다.
- Parent 문서는 실행 중 메모리에 보관되므로 질문 전에 같은 PDF 집합으로 스크립트를 실행해야 합니다.

자세한 데이터 준비 방법은 [datasets/README.md](datasets/README.md)를 참고하세요.
