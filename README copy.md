# RAG System

문서 기반 검색 증강 생성(RAG) 시스템 실습 자료입니다.

## 환경 설정

### 1. uv 설치

#### Windows (PowerShell)

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### macOS / Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

### 2. 가상환경 생성 및 패키지 설치

```bash
cd smu-ai-service-bootcamp
cd rag-system

# pyproject.toml을 기반으로 가상환경 생성 및 패키지 설치
uv sync

# 가상환경 활성화 (Windows)
.venv\Scripts\activate

# 가상환경 활성화 (macOS/Linux)
source .venv/bin/activate
```

---

### 3. Jupyter Notebook 커널 등록

VS Code에서 Jupyter Notebook을 사용하려면 커널을 등록해야 합니다.

#### Windows

```powershell
.venv\Scripts\python.exe -m ipykernel install --user --name=ai-service-rag --display-name="ai service rag"
```

#### macOS/Linux

```bash
.venv/bin/python -m ipykernel install --user --name=ai-service-rag --display-name="ai service rag"
```

커널 등록 후 **VS Code를 리로드**하면 노트북에서 "ai service rag" 커널을 선택할 수 있습니다.


### 4. 환경 변수 설정

루트 디렉토리에 `.env` 파일을 생성하고 다음 내용을 작성하세요:

```bash
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Qdrant Cloud 설정
QDRANT_URL=https://your-cluster-url.cloud.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key_here

# Supabase 설정
SUPABASE_DB_URL=postgresql://postgres.[PROJECT_ID]:[PASSWORD]@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres
```

### 5. Qdrant Cloud 설정 (RAG)

[Qdrant Cloud](https://cloud.qdrant.io/signup) 가입 → Free Cluster 생성 → URL과 API Key를 `.env`에 추가

### 6. Supabase 설정 (Text2SQL)

[Supabase](https://supabase.com/) 가입 → New Project 생성 → Settings → Database → Connection string (URI) 복사 → `.env`에 추가

**CSV 데이터 업로드**: Table Editor → Import data from CSV


### 7. LangGraph Studio 실행

```bash
# LangGraph Studio 시작
uv run langgraph dev
```

브라우저에서 `http://127.0.0.1:2024` 자동 열림

### 8. Streamlit 웹 앱 실행

```bash
uv run streamlit run src/demo/streamlit_example.py
```

브라우저에서 `http://localhost:8501` 자동 열림