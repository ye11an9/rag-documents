from langchain.agents import create_agent
# TODO: 팀에서 생성한 커스텀 도구를 import 하세요
# 예시: from custom_tools import CUSTOM_TOOLS
from tools import FILE_TOOLS


def create_coding_agent():
    # TODO: 시스템 프롬프트를 팀 도메인에 맞게 수정하세요
    # 아래는 코딩 에이전트 예시입니다.
    # 팀의 도메인(쇼핑, 법령, 의료, 여행 등)에 맞게 변경하세요.

    system_prompt = """당신은 Python 코딩 작업을 도와주는 전문 에이전트입니다.

다음과 같은 파일 시스템 작업을 수행할 수 있습니다:
- 파일 읽기: 파일의 내용을 읽어옵니다
- 파일 쓰기: 파일에 새로운 내용을 작성합니다 (없으면 생성, 있으면 덮어쓰기)
- 파일 삭제: 불필요한 파일을 삭제합니다
- 디렉터리 생성: 새로운 폴더를 만듭니다
- 디렉터리 목록: 폴더 내의 파일과 하위 폴더를 조회합니다
- Python 코드 실행: Python 코드를 실행하고 결과를 확인합니다

사용자의 요청을 정확히 이해하고, 적절한 도구를 사용하여 작업을 수행하세요.
파일 경로는 상대 경로 또는 절대 경로를 모두 지원합니다.

작업 수행 시 다음 사항을 유의하세요:
1. 파일을 수정하기 전에 먼저 읽어서 내용을 확인하세요
2. 중요한 파일을 삭제하기 전에 사용자에게 확인을 요청하세요
3. 코드 실행 시 보안과 안전성을 고려하세요
4. 에러가 발생하면 명확하게 설명하고 해결 방법을 제시하세요

모든 응답은 한글로 작성하세요."""

    # TODO: 에이전트에 사용할 도구 리스트를 변경하세요
    # 팀에서 생성한 커스텀 도구를 사용하려면:
    # tools = CUSTOM_TOOLS
    # 또는 기존 도구와 함께 사용:
    # tools = FILE_TOOLS + CUSTOM_TOOLS

    # 에이전트 생성
    agent_executor = create_agent(
        model="gpt-5.4-mini",
        tools=FILE_TOOLS,  # TODO: 여기를 팀의 도구로 변경
        system_prompt=system_prompt
    )

    return agent_executor


# LangGraph Studio에서 사용할 에이전트 내보내기
agent = create_coding_agent()
