"""프로젝트 공통 환경변수 로딩 설정."""

from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"


def load_project_env() -> Path:
    """프로젝트 루트의 .env를 명시적으로 읽고 기존 환경변수보다 우선한다."""
    if not ENV_PATH.is_file():
        raise FileNotFoundError(f"환경변수 파일을 찾을 수 없습니다: {ENV_PATH}")

    load_dotenv(dotenv_path=ENV_PATH, override=True)
    return ENV_PATH
