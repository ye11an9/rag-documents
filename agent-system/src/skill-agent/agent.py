from langchain.agents import create_agent

from tools import TOOLS
from middleware import SkillMiddleware


def create_skill_agent():
    system_prompt=(
        "당신은 사용자를 도와주는 에이전트입니다."
    )

    # 스킬 미들웨어 초기화
    skill_middleware = SkillMiddleware()

    agent_executor = create_agent(
        model="gpt-5.4-mini",
        tools=TOOLS,
        system_prompt=system_prompt,
        middleware=[skill_middleware],
    )

    return agent_executor


agent = create_skill_agent()
