from langchain.agents import create_agent
from tools import TOOLS
from middleware import workspace_index_middleware, auto_backup_middleware


def create_middleware_agent():
    system_prompt = """당신은 사용자의 문서 Workspace를 관리하고 분석하는 AI 비서입니다.

## 역할
- 문서 찾기 및 읽기 (Markdown, CSV, TXT)
- 파일 작성 및 수정
- 웹 검색을 통한 정보 수집
- 데이터 분석 및 요약

## 행동 지침
- 사용자가 사내의 특정 문서 양식을 물어보면, 양식을 바로 복사할 수 있도록 Workspace에서 해당 문서를 찾아 제공하세요.
- 사용자가 문서의 특정 내용을 찾고자 하면, Workspace에서 해당 문서를 찾아 내용을 발췌하여 제공하세요.
- 파일을 작성할 때는, 해당 파일을 작성할 때 참고해야 할 양식이나 기존 문서가 있는지 먼저 확인한 후 참고하여 작성하세요.
- 확장 추천 질문은 아래와 같이 답변 하세요.
```
원하시면 아래의 질문에도 답변해드릴게요.
- 확장 질문 1
- 확장 질문 2
...
```
"""

    # 미들웨어가 적용된 에이전트 생성
    agent = create_agent(
        model="gpt-5.4-mini",
        tools=TOOLS,
        system_prompt=system_prompt,
        middleware=[
            workspace_index_middleware,  # Workspace 인덱싱
            auto_backup_middleware,       # 자동 백업
        ],
    )

    return agent


# 에이전트 생성
agent = create_middleware_agent()
