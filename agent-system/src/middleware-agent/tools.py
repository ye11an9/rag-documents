from langchain.tools import tool
from langchain_tavily import TavilySearch # type: ignore
import os


# ============================================
# 파일 시스템 도구
# ============================================

@tool(parse_docstring=True)
def read_file(file_path: str) -> str:
    """파일의 내용을 읽어서 반환합니다.

    Args:
        file_path: 읽을 파일의 경로

    Returns:
        파일 내용 또는 오류 메시지
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return f"파일: {file_path}\n\n{content}"
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

        return f"성공: 파일이 작성되었습니다: {file_path}"
    except Exception as e:
        return f"오류: {str(e)}"


@tool(parse_docstring=True)
def edit_file(file_path: str, old_string: str, new_string: str) -> str:
    """파일에서 특정 문자열을 찾아 새로운 문자열로 교체합니다.

    Args:
        file_path: 수정할 파일의 경로
        old_string: 찾을 문자열
        new_string: 교체할 문자열

    Returns:
        성공 메시지 또는 오류 메시지
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if old_string not in content:
            return f"오류: 파일에서 지정된 문자열을 찾을 수 없습니다: {file_path}"

        new_content = content.replace(old_string, new_string)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return f"성공: 파일이 수정되었습니다: {file_path}"
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

        items = os.listdir(dir_path)

        if not items:
            return f"디렉터리가 비어있습니다: {dir_path}"

        # 파일과 폴더 분류
        folders = []
        files = []

        for item in sorted(items):
            item_path = os.path.join(dir_path, item)
            if os.path.isdir(item_path):
                folders.append(f"📁 {item}/")
            else:
                files.append(f"📄 {item}")

        result = [f"디렉터리: {dir_path}\n"]

        if folders:
            result.append("폴더:")
            result.extend(folders)
            result.append("")

        if files:
            result.append("파일:")
            result.extend(files)

        return "\n".join(result)
    except Exception as e:
        return f"오류: {str(e)}"


# ============================================
# 문서 읽기 도구
# ============================================

@tool(parse_docstring=True)
def read_csv(file_path: str, max_rows: int = 50) -> str:
    """CSV 파일의 데이터를 읽습니다.

    Args:
        file_path: CSV 파일 경로
        max_rows: 읽을 최대 행 수 (기본값: 50)

    Returns:
        파일 내용 또는 오류 메시지
    """
    try:
        if not os.path.exists(file_path):
            return f"오류: 파일을 찾을 수 없습니다: {file_path}"

        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        total_lines = len(lines)
        displayed_lines = min(total_lines, max_rows)
        content = "".join(lines[:displayed_lines])

        result = f"파일: {file_path}\n타입: CSV\n총 {total_lines}줄 (표시: {displayed_lines}줄)\n\n{content}"

        if total_lines > max_rows:
            result += f"\n\n... ({total_lines - max_rows}줄 생략)"

        return result
    except Exception as e:
        return f"오류: {str(e)}"


# ============================================
# 문서 검색 도구
# ============================================

@tool(parse_docstring=True)
def search_workspace(query: str) -> str:
    """workspace에서 파일명에 특정 키워드가 포함된 파일을 검색합니다.

    Args:
        query: 검색할 키워드

    Returns:
        검색 결과 목록
    """
    try:
        cwd = os.getcwd()
        results = []

        # 지원하는 확장자
        extensions = [".md", ".txt", ".csv"]

        # workspace 검색
        for root, dirs, files in os.walk(cwd):
            # 제외할 디렉터리
            dirs[:] = [d for d in dirs if not d.startswith('.')
                       and d not in ['__pycache__', 'node_modules', 'venv', '.cache']]

            level = root.replace(cwd, '').count(os.sep)
            if level > 3:
                continue

            for file in files:
                if file.startswith('.'):
                    continue

                file_ext = os.path.splitext(file)[1].lower()

                # 파일명에 query가 포함되어 있는지 확인
                if file_ext in extensions and query.lower() in file.lower():
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, cwd)
                    results.append(f"  • {rel_path}")

        if not results:
            return f"검색 결과 없음: '{query}'에 해당하는 파일을 찾을 수 없습니다."

        output = [f"🔍 검색어: {query}", f"📊 총 {len(results)}개 파일 발견\n"]
        output.extend(results)

        return "\n".join(output)
    except Exception as e:
        return f"오류: {str(e)}"


# ============================================
# 웹 검색 도구
# ============================================

# Tavily Search 도구 (웹 검색)
web_search = TavilySearch(
    max_results=3,
    topic="general",
    description="인터넷에서 최신 정보를 검색합니다. 실시간 정보나 최근 뉴스가 필요할 때 사용하세요."
)


# ============================================
# 도구 목록
# ============================================

TOOLS = [
    # 파일 시스템
    read_file,
    write_file,
    edit_file,
    delete_file,
    create_directory,
    list_directory,
    # 문서 읽기
    read_csv,
    # 검색
    search_workspace,
    web_search,
]
