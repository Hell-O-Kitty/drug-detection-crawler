import os
from pathlib import Path
import shutil
from dotenv import load_dotenv

# .env 로드
load_dotenv()

# 프로젝트 경로
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "initial_crawling_data"
RAW_DIR = DATA_DIR / "raw"
HTML_SAVE_DIR = RAW_DIR / "html"
DOWNLOADED_IMAGE_DIR = DATA_DIR / "downloaded_images"
DOWNLOADED_MEDIA_DIR = DATA_DIR / "downloaded_image"

# 중간/결과 데이터 경로
RAW_JSON_PATH = DATA_DIR / "collected_elements.json"
PARSED_JSON_PATH = DATA_DIR / "tweet_datas.json"
TEXT_CSV_PATH = DATA_DIR / "x_crawling_drugs_text.csv"
TEXT_CSV_ORIGINALS_PATH = DATA_DIR / "x_crawling_drugs_text_originals.json"
LEGACY_TWEETS_CSV_PATH = DATA_DIR / "tweets.csv"

# Media download settings
MEDIA_DOWNLOAD_CSV_PATH = Path(os.getenv("MEDIA_DOWNLOAD_CSV_PATH", TEXT_CSV_PATH))
MEDIA_DOWNLOAD_DIR = Path(os.getenv("MEDIA_DOWNLOAD_DIR", DOWNLOADED_MEDIA_DIR))
MEDIA_DOWNLOAD_START_ID = int(os.getenv("MEDIA_DOWNLOAD_START_ID", 1))
MEDIA_DOWNLOAD_END_ID = os.getenv("MEDIA_DOWNLOAD_END_ID")
MEDIA_DOWNLOAD_END_ID = int(MEDIA_DOWNLOAD_END_ID) if MEDIA_DOWNLOAD_END_ID else None
MEDIA_DOWNLOAD_RETRY_COUNT = int(os.getenv("MEDIA_DOWNLOAD_RETRY_COUNT", 3))
MEDIA_DOWNLOAD_TIMEOUT = int(os.getenv("MEDIA_DOWNLOAD_TIMEOUT", 20))
MEDIA_DOWNLOAD_ON_SAVE = os.getenv("MEDIA_DOWNLOAD_ON_SAVE", "true").lower() not in {
    "0",
    "false",
    "no",
}
MEDIA_DOWNLOAD_COLUMNS = [
    column.strip()
    for column in os.getenv(
        "MEDIA_DOWNLOAD_COLUMNS",
        "image_urls,video_video_blob_url,video_video_poster_url,video_video_source_url",
    ).split(",")
    if column.strip()
]

# 이전 이름과의 호환을 위한 alias
RAW_JSON_DIR = DATA_DIR
DOWNLOADED_IMAGE_PATH = DOWNLOADED_IMAGE_DIR

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

# 포트 (env -> 기본값)
DEBUG_PORT = int(os.getenv("DEBUG_PORT", 9222))

# Chrome 프로필 경로
USER_DATA_DIR = Path(os.getenv("USER_DATA_DIR", Path.home() / "selenium_profile"))

# 크롤링 단위 (HTML_TAG)
HTML_TAG = os.getenv("HTML_TAG", "article")

# 원본 소스 이름
SOURCE_NAME = os.getenv("SOURCE_NAME", "twitter_feed")

