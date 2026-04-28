import os
from pathlib import Path
import shutil
from dotenv import load_dotenv

# .env 로드
load_dotenv()

# 프로젝트 루트
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

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

# HTML 저장 위치
HTML_SAVE_DIR = BASE_DIR/"initial_crawling_data"/"raw"/"html"

# 원본 JSON 저장 위치
RAW_JSON_DIR = BASE_DIR / "initial_crawling_data"
RAW_JSON_PATH = BASE_DIR / "initial_crawling_data" / "collected_elements.json"

# 크롤링 단위 (HTML_TAG)
HTML_TAG = os.getenv("HTML_TAG", "article")

# 원본 소스 이름
SOURCE_NAME = os.getenv("SOURCE_NAME", "twitter_feed")

# tweet_datas.json (마약 관련)
# PARSED_JSON_PATH = RAW_JSON_DIR / "tweet_datas.json"
# INPUT_JSON_PATH  = RAW_JSON_DIR / "tweet_datas.json"
# OUTPUT_CSV_PATH = RAW_JSON_DIR / "tweets.csv"

# tweet_datas.json (의약품 관련 메세지)
PARSED_JSON_PATH = RAW_JSON_DIR / "tweet_medi_datas.json"
INPUT_JSON_PATH  = RAW_JSON_DIR / "tweet_medi_datas.json"
OUTPUT_CSV_PATH = RAW_JSON_DIR / "tweets_medi.csv"