# Document Workspace Agent

### LangGraph Studio 실행

#### Windows (PowerShell)

```powershell
$env:PYTHONUTF8=1; uv run langgraph dev --no-reload --allow-blocking
```

#### Mac/Linux (bash/zsh)

```
PYTHONUTF8=1 uv run langgraph dev --no-reload --allow-blocking
```


## 파일 구조

```
middleware-agent/
├── agent.py              # Agent 정의
├── middleware.py         # 커스텀 미들웨어
├── tools.py              # 도구 정의
└── README.md
```

## 도구 목록

### 파일 시스템
- `read_file`: 파일 읽기
- `write_file`: 파일 작성
- `edit_file`: 파일 수정
- `delete_file`: 파일 삭제
- `create_directory`: 디렉터리 생성
- `list_directory`: 디렉터리 목록

### 문서 읽기
- `read_markdown`: Markdown 파일 읽기
- `read_csv`: CSV 파일 읽기

### 검색
- `search_workspace`: workspace 파일 검색
- `web_search`: 웹 검색 (Tavily)


## 미들웨어 동작 방식

### Workspace Index Middleware

```python
@before_agent
def workspace_index_middleware(state, runtime):
    # workspace의 모든 MD, CSV, TXT 파일 스캔
    # 파일 목록을 SystemMessage로 LLM에 전달
    # LLM은 파일 구조를 즉시 파악 가능
```

### Auto Backup Middleware

```python
@wrap_tool_call
async def auto_backup_middleware(request, handler):
    # edit_file 호출 시 자동으로 백업 생성
    # backup/ 디렉터리에 파일명_YYYYMMDD_HHMMSS.확장자 형식으로 저장
    # 예: meeting.md → backup/meeting_20260730_143022.md
    # 백업 후 원본 edit_file 실행
```

### 테스트 질문

```
- "workspace에 어떤 파일들이 있어?"
- "회의록 찾아줘"
- "8월 회의록 요약해줘"
- "CRM 데이터에서 VIP 고객은?"
- "웹에서 LangGraph 검색해줘"
```