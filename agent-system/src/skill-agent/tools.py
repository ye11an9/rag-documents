from langchain.tools import tool
from typing import TypedDict
import subprocess
import sys
import os
import requests
from langchain_tavily import TavilySearch # type: ignore


DEFAULT_CHUNK_SIZE = 15_000


# ============================================
# 스킬 구조 정의
# ============================================

class Skill(TypedDict):
    """
    Progressive Disclosure 패턴에서 사용되는 스킬 구조

    Attributes:
        name: 스킬의 고유 식별자
        description: 시스템 프롬프트에 표시될 1-2문장 설명
        content: load_skill 도구로 로드되는 전체 스킬 내용
    """
    name: str
    description: str
    content: str  # 실제로는 파일에서 on-demand로 로드됨


# ============================================
# URL 가져오기 도구
# ============================================


@tool
def fetch_url(
    url: str,
    offset: int = 0,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> str:
    """
    URL의 내용을 페이지(chunk) 단위로 가져옵니다.

    Progressive Disclosure 패턴에서 외부 리소스를 가져오는 데 사용됩니다.
    긴 문서는 chunk 단위로 나누어 읽을 수 있습니다.

    **사용 시나리오:**
    1. 스킬에서 "fetch_url로 문서 가져오기" 지시
    2. 첫 번째 chunk 읽기 (offset=0)
    3. 더 필요하면 다음 offset으로 이어서 읽기

    반환값에 "남은 내용 존재: True"가 있으면 부족한 정보를 더 읽기 위해
    fetch_url()을 다시 호출하여 offset=다음 offset으로 이어서 읽어야 합니다.

    Args:
        url: 가져올 URL (예: https://docs.langchain.com/llms.txt)
        offset: 읽기 시작할 문자 위치 (기본값: 0)
        chunk_size: 한 번에 가져올 문자 수 (기본값: 15,000)

    Returns:
        현재 chunk와 다음 offset 정보를 포함한 문자열

    Examples:
        >>> # 첫 번째 청크 가져오기
        >>> result = fetch_url("https://docs.langchain.com/llms.txt")
        >>> # 다음 청크 가져오기 (결과에 next_offset이 있는 경우)
        >>> result2 = fetch_url("https://docs.langchain.com/llms.txt", offset=15000)
    """

    print(f"\n{'=' * 70}")
    print(f"🌐 URL 가져오는 중")
    print(f"URL         : {url}")
    print(f"Offset      : {offset}")
    print(f"Chunk Size  : {chunk_size}")
    print(f"{'=' * 70}\n")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        text = response.text
        total_length = len(text)

        if offset >= total_length:
            return (
                f"문서 끝에 도달했습니다.\n"
                f"전체 길이: {total_length}\n"
                f"offset={offset}"
            )

        end = min(offset + chunk_size, total_length)

        chunk = text[offset:end]

        has_more = end < total_length
        next_offset = end if has_more else None

        print(
            f"전체 {total_length:,}자 중 "
            f"{offset:,} ~ {end:,} 반환 "
            f"({len(chunk):,}자)"
        )

        return f"""# URL Chunk

URL: {url}

전체 길이: {total_length}
현재 범위: {offset} ~ {end}

다음 offset: {next_offset}
남은 내용 존재: {has_more}

--------------------
{chunk}
"""

    except requests.RequestException as e:
        return f"URL 가져오기 실패: {e}"



# ============================================
# 파일 시스템 도구
# ============================================

@tool(parse_docstring=True)
def read_file(file_path: str) -> str:
    """파일의 내용을 읽어서 반환합니다.

    Args:
        file_path: 읽을 파일의 경로 (상대 경로 또는 절대 경로)

    Returns:
        파일 내용 또는 오류 메시지
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        line_count = len(content.split("\n"))
        return f"파일: {file_path}\n총 {line_count}줄\n\n{content}"
    except FileNotFoundError:
        return f"오류: 파일을 찾을 수 없습니다: {file_path}"
    except PermissionError:
        return f"오류: 파일에 대한 읽기 권한이 없습니다: {file_path}"
    except Exception as e:
        return f"오류: {str(e)}"


@tool(parse_docstring=True)
def write_file(file_path: str, content: str) -> str:
    """파일에 내용을 작성합니다. 파일이 없으면 생성하고, 있으면 덮어씁니다.

    Args:
        file_path: 작성할 파일의 경로
        content: 파일에 쓸 내용

    Returns:
        성공 메시지 또는 오류 메시지
    """
    try:
        # 디렉터리가 없으면 생성
        os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else ".", exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        line_count = len(content.split("\n"))
        return f"성공: 파일이 작성되었습니다: {file_path} (총 {line_count}줄)"
    except PermissionError:
        return f"오류: 파일에 대한 쓰기 권한이 없습니다: {file_path}"
    except Exception as e:
        return f"오류: {str(e)}"


@tool(parse_docstring=True)
def delete_file(file_path: str) -> str:
    """파일을 삭제합니다.

    Args:
        file_path: 삭제할 파일의 경로

    Returns:
        성공 메시지 또는 오류 메시지
    """
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
            return f"성공: 파일이 삭제되었습니다: {file_path}"
        else:
            return f"오류: 파일을 찾을 수 없습니다: {file_path}"
    except PermissionError:
        return f"오류: 파일에 대한 삭제 권한이 없습니다: {file_path}"
    except Exception as e:
        return f"오류: {str(e)}"


@tool(parse_docstring=True)
def create_directory(dir_path: str) -> str:
    """새로운 디렉터리를 생성합니다.

    Args:
        dir_path: 생성할 디렉터리의 경로

    Returns:
        성공 메시지 또는 오류 메시지
    """
    try:
        os.makedirs(dir_path, exist_ok=True)
        return f"성공: 디렉터리가 생성되었습니다: {dir_path}"
    except PermissionError:
        return f"오류: 디렉터리 생성 권한이 없습니다: {dir_path}"
    except Exception as e:
        return f"오류: {str(e)}"


@tool(parse_docstring=True)
def list_directory(dir_path: str = ".") -> str:
    """디렉터리의 파일과 폴더 목록을 반환합니다.

    Args:
        dir_path: 조회할 디렉터리 경로 (기본값: 현재 디렉터리)

    Returns:
        파일 및 폴더 목록 또는 오류 메시지
    """
    try:
        if not os.path.exists(dir_path):
            return f"오류: 디렉터리를 찾을 수 없습니다: {dir_path}"

        if not os.path.isdir(dir_path):
            return f"오류: {dir_path}는 디렉터리가 아닙니다"

        items = os.listdir(dir_path)

        if not items:
            return f"디렉터리가 비어있습니다: {dir_path}"

        # 파일과 폴더 분류
        folders = []
        files = []

        for item in sorted(items):
            item_path = os.path.join(dir_path, item)
            if os.path.isdir(item_path):
                folders.append(f"[폴더] {item}/")
            else:
                size = os.path.getsize(item_path)
                files.append(f"[파일] {item} ({size} bytes)")

        result = f"디렉터리: {dir_path}\n\n"

        if folders:
            result += "폴더:\n" + "\n".join(folders) + "\n\n"

        if files:
            result += "파일:\n" + "\n".join(files)

        return result

    except PermissionError:
        return f"오류: 디렉터리에 대한 읽기 권한이 없습니다: {dir_path}"
    except Exception as e:
        return f"오류: {str(e)}"


# ============================================
# 스킬 관련 도구
# ============================================

@tool(parse_docstring=True)
def load_skill(skill_name: str) -> str:
    """특정 도메인에 대한 전문 지식 스킬을 로드합니다.

    Progressive Disclosure 패턴의 핵심 도구로, 필요한 스킬의 상세 내용을
    on-demand로 로드합니다.

    스킬은 특정 주제에 대한 상세한 정보, 사용 패턴, 프로세스 등을 포함합니다.
    스킬을 로드하면 해당 스킬에 정의된 프로세스를 따라 전문적인 작업이 가능해집니다.

    **중요**: 스킬이 로드되면 그 안에 정의된 프로세스를 반드시 따라야 합니다.
    스킬은 단순 참고 자료가 아니라 실행 지침입니다.

    Args:
        skill_name: 로드할 스킬 이름 (예: 'langgraph-docs', 'my-skill-name')

    Returns:
        스킬의 전체 내용 (SKILL.md 파일) 또는 오류 메시지

    Examples:
        >>> # 사용자가 "LangGraph에 대해 알려줘"라고 질문
        >>> # 1. 시스템 프롬프트에서 langgraph-docs 스킬 설명 확인
        >>> # 2. load_skill('langgraph-docs') 호출
        >>> # 3. 로드된 프로세스를 따라 fetch_url로 문서 가져오기
        >>> # 4. 답변 생성
    """
    try:
        # 스킬 디렉터리 경로
        skills_dir = os.path.join(os.path.dirname(__file__), "skills")
        skill_path = os.path.join(skills_dir, skill_name, "SKILL.md")

        # 스킬 파일이 존재하는지 확인
        if not os.path.exists(skill_path):
            # 사용 가능한 스킬 목록 조회
            available_skills = []
            if os.path.exists(skills_dir):
                for item in os.listdir(skills_dir):
                    item_path = os.path.join(skills_dir, item)
                    if os.path.isdir(item_path):
                        skill_file = os.path.join(item_path, "SKILL.md")
                        if os.path.exists(skill_file):
                            available_skills.append(item)

            error_msg = f"오류: '{skill_name}' 스킬을 찾을 수 없습니다."
            if available_skills:
                error_msg += f"\n\n사용 가능한 스킬:\n" + "\n".join(f"- {s}" for s in available_skills)
            else:
                error_msg += "\n\n현재 사용 가능한 스킬이 없습니다."

            return error_msg

        # 스킬 파일 읽기
        with open(skill_path, "r", encoding="utf-8") as f:
            skill_content = f.read()

        # 로드 완료 메시지와 함께 스킬 내용 반환
        result = (
            f"✅ [스킬 로드 완료: {skill_name}]\n\n"
            f"{'=' * 70}\n"
            f"{skill_content}\n"
            f"{'=' * 70}\n\n"
            f"**다음 단계**: 위 스킬에 정의된 프로세스를 단계별로 따라 실행하세요.\n"
        )

        return result

    except PermissionError:
        return f"오류: 스킬 파일에 대한 읽기 권한이 없습니다: {skill_path}"
    except Exception as e:
        return f"오류: 스킬 로드 중 문제가 발생했습니다: {str(e)}"


FILE_TOOLS = [
    read_file,
    write_file,
    delete_file,
    create_directory,
    list_directory
]

web_search = TavilySearch(
    max_results=3,
    topic="general",
    description="인터넷에서 최신 정보를 검색합니다. 실시간 정보나 최근 뉴스가 필요할 때 사용하세요."
)

TOOLS = FILE_TOOLS + [fetch_url, load_skill, web_search]
