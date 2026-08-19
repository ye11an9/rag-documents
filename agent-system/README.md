# Agent System

LangChain create_agent 기반 에이전트 시스템 구현 실습 자료입니다.

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
cd agent-system

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
.venv\Scripts\python.exe -m ipykernel install --user --name=ai-service-agent --display-name="ai service agent"
```

#### macOS/Linux

```bash
.venv/bin/python -m ipykernel install --user --name=ai-service-agent --display-name="ai service agent"
```

커널 등록 후 **VS Code를 리로드**하면 노트북에서 "ai service agent" 커널을 선택할 수 있습니다.


### 4. 환경 변수 설정

루트 디렉토리에 `.env` 파일을 생성하고 다음 내용을 작성하세요:

```bash
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

### 5. LangGraph Studio 실행

```bash
# LangGraph Studio 시작
uv run langgraph dev
```

#### Windows (PowerShell)

```powershell
$env:PYTHONUTF8=1; uv run langgraph dev --no-reload --allow-blocking
```

#### Mac/Linux (bash/zsh)

```
PYTHONUTF8=1 uv run langgraph dev --no-reload --allow-blocking
```

브라우저에서 `http://127.0.0.1:2024` 자동 열림