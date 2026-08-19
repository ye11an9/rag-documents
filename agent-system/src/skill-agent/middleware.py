from langchain.agents.middleware import ModelRequest, ModelResponse, AgentMiddleware
from langchain.messages import SystemMessage
from typing import Callable
import os
import re
from typing import Awaitable


def parse_skill_metadata():
    """
    skills 디렉터리의 모든 SKILL.md 파일에서 name과 description을 추출합니다.

    Returns:
        스킬 정보가 담긴 딕셔너리 리스트
        [{"name": "skill-name", "description": "..."}, ...]
    """
    skills = []
    skills_dir = os.path.join(os.path.dirname(__file__), "skills")

    if not os.path.exists(skills_dir):
        return skills

    for item in os.listdir(skills_dir):
        item_path = os.path.join(skills_dir, item)
        if os.path.isdir(item_path):
            skill_file = os.path.join(item_path, "SKILL.md")
            if os.path.exists(skill_file):
                try:
                    with open(skill_file, "r", encoding="utf-8") as f:
                        content = f.read()

                    # YAML frontmatter 파싱
                    # ---로 시작하고 ---로 끝나는 부분 추출
                    frontmatter_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)

                    if frontmatter_match:
                        frontmatter = frontmatter_match.group(1)

                        # name과 description 추출
                        name_match = re.search(r'name:\s*(.+)', frontmatter)
                        desc_match = re.search(r'description:\s*(.+)', frontmatter)

                        name = name_match.group(1).strip() if name_match else item
                        description = desc_match.group(1).strip() if desc_match else "스킬 설명 없음"

                        skills.append({
                            "name": name,
                            "description": description
                        })
                    else:
                        # frontmatter가 없는 경우, 기본값 사용
                        skills.append({
                            "name": item,
                            "description": f"{item} 스킬"
                        })

                except Exception as e:
                    print(f"스킬 {item} 파싱 중 오류: {e}")
                    continue

    return skills


# 전역 변수로 SKILLS 정의
SKILLS = parse_skill_metadata()


class SkillMiddleware(AgentMiddleware):
    """
    에이전트의 시스템 프롬프트에 사용 가능한 스킬 목록을 주입하는 미들웨어입니다.

    이 미들웨어는:
    1. skills 디렉터리의 모든 SKILL.md 파일에서 메타데이터를 파싱
    2. 스킬 목록을 시스템 프롬프트에 추가
    3. 에이전트가 적절한 스킬을 선택할 수 있도록 가이드 제공
    4. Progressive Disclosure 패턴 지원 - 스킬 설명만 미리 제공하고,
       상세 내용은 load_skill 도구를 통해 on-demand로 로드
    """
    def __init__(self):
        """미들웨어를 초기화하고 스킬 프롬프트를 생성합니다."""
        # SKILLS 리스트에서 스킬 설명 생성
        skills_list = []
        for skill in SKILLS:
            skills_list.append(
                f"- **{skill['name']}**: {skill['description']}"
            )

        if skills_list:
            self.skills_prompt = "\n".join(skills_list)
        else:
            self.skills_prompt = "현재 등록된 스킬이 없습니다."

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """
        모델 호출을 가로채어 시스템 프롬프트에 스킬 정보를 주입합니다.

        Args:
            request: 원본 모델 요청
            handler: 실제 모델 호출을 처리하는 핸들러

        Returns:
            수정된 요청으로 호출한 모델 응답
        """
        # 스킬 정보를 시스템 메시지에 추가
        skills_addendum = (
            f"\n\n## 사용 가능한 스킬 (Available Skills)\n\n{self.skills_prompt}\n\n"
            "**중요**: 특정 도메인에 대한 질문이나 작업 요청이 들어오면, "
            "위 스킬 목록에서 관련된 스킬을 찾아 `load_skill` 도구를 사용하여 "
            "해당 스킬의 상세 프로세스를 로드하세요. "
        )

        # 기존 시스템 메시지의 content_blocks에 추가
        new_content = list(request.system_message.content_blocks) + [
            {"type": "text", "text": skills_addendum}
        ]
        new_system_message = SystemMessage(content=new_content)

        # 수정된 요청 생성 및 핸들러 호출
        modified_request = request.override(system_message=new_system_message)
        return handler(modified_request)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        """
        비동기 모델 호출을 가로채어 시스템 프롬프트에 스킬 정보를 주입합니다.

        LangGraph Studio나 astream(), ainvoke() 등 비동기 컨텍스트에서 사용됩니다.

        Args:
            request: 원본 모델 요청
            handler: 실제 모델 호출을 처리하는 비동기 핸들러

        Returns:
            수정된 요청으로 호출한 모델 응답
        """
        # 스킬 정보를 시스템 메시지에 추가
        skills_addendum = (
            f"\n\n## 사용 가능한 스킬 (Available Skills)\n\n{self.skills_prompt}\n\n"
            "**중요**: 특정 도메인에 대한 질문이나 작업 요청이 들어오면, "
            "위 스킬 목록에서 관련된 스킬을 찾아 `load_skill` 도구를 사용하여 "
            "해당 스킬의 상세 프로세스를 로드하세요. "
        )

        # 기존 시스템 메시지의 content_blocks에 추가
        new_content = list(request.system_message.content_blocks) + [
            {"type": "text", "text": skills_addendum}
        ]
        new_system_message = SystemMessage(content=new_content)

        # 수정된 요청 생성 및 핸들러 호출
        modified_request = request.override(system_message=new_system_message)
        return await handler(modified_request)
