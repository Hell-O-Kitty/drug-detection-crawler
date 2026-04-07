import os
from pathlib import Path
import shutil
from dotenv import load_dotenv

# .env 로드
load_dotenv()

# 프로젝트 루트
BASE_DIR = Path(__file__).resolve().parent.parent.parent

def get_chrome_path():
    path = (
        shutil.which("chrome")
        or shutil.which("chrome.exe")
        or shutil.which("google-chrome")
        or shutil.which("chromium")
    )

    if path:
        return path

    candidates = [
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    ]

    for p in candidates:
        if p.exists():
            return str(p)

    return None

# Chrome 경로 (env -> 자동 탐색 -> fallback)
CHROME_PATH = os.getenv("CHROME_PATH") or get_chrome_path()

if CHROME_PATH is None:
    raise FileNotFoundError("Chrome 실행 파일을 찾을 수 없습니다.")

# 포트 (env -> 기본값)
DEBUG_PORT = int(os.getenv("DEBUG_PORT", 9222))

# 프로필 경로
USER_DATA_DIR = Path.home() / "selenium_profile"
