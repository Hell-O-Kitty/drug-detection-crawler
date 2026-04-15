import requests
import json
import os
import csv
import base64
import mimetypes
from pathlib import Path
from urllib.parse import urlparse
import re

CSV_FIELDS = [
    "num",
    "nickname",
    "user_id",
    "date",
    "text",
    "counts_reply",
    "counts_retweet",
    "counts_like",
    "counts_view",
    "image_urls",
    "hashtags",
    "video_video_blob_url",
    "video_video_poster_url",
    "video_video_source_url",
]


# -----------------------------
# HTML 저장
# -----------------------------
def save_articles(parent_file_name, save_folder_path, articles):
    saved_files = []

    os.makedirs(save_folder_path, exist_ok=True)
    print(f"ready to save : {save_folder_path}")

    for idx, article_html in enumerate(articles, start=1):
        file_name = f"article_{parent_file_name}_{idx}.html"
        file_path = os.path.join(save_folder_path, file_name)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(article_html)

        saved_files.append(file_path)
        print(f"saved {file_name} : {file_path}")

    return saved_files


# -----------------------------
# JSON 저장
# -----------------------------
def save_to_json(data, path="result.json"):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            existing_data = []
    else:
        existing_data = []

    if not isinstance(existing_data, list):
        existing_data = [existing_data]

    if isinstance(data, list):
        existing_data.extend(data)
    else:
        existing_data.append(data)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)

    print(f"{len(existing_data)}개 데이터 저장 완료")


# -----------------------------
# 기본 유틸
# -----------------------------
def ensure_dir(directory: str) -> None:
    os.makedirs(directory, exist_ok=True)


def read_json_file(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_existing_csv_rows(csv_path: str):
    if not os.path.exists(csv_path):
        return []

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def write_csv_rows(csv_path: str, rows: list[dict]) -> None:
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def append_csv_row(csv_path: str, row: dict) -> None:
    file_exists = os.path.exists(csv_path)

    with open(csv_path, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)

        if not file_exists or os.path.getsize(csv_path) == 0:
            writer.writeheader()

        writer.writerow(row)

def get_last_num(rows: list[dict]) -> int:
    nums = []
    for row in rows:
        try:
            nums.append(int(row.get("num", 0)))
        except (TypeError, ValueError):
            print(f"[num 파싱 스킵] invalid num={row.get('num')!r}")
    return max(nums, default=0)
  
def contains_korean(text: str) -> bool:
    if not text:
        return False
    return bool(re.search(r"[가-힣]", text))

# -----------------------------
# URL/파일/이미지 처리
# -----------------------------
def get_extension_from_url_or_response(url: str, response: requests.Response | None = None) -> str:
    parsed = urlparse(url)
    path = parsed.path
    ext = Path(path).suffix.lower()

    if ext:
        return ext

    if response is not None:
        content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
        guessed = mimetypes.guess_extension(content_type)
        if guessed:
            return guessed

    return ".jpg"


def download_file(url: str, save_path: str, timeout: int = 15) -> str | None:
    if not url:
        return None

    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        ext = get_extension_from_url_or_response(url, response)
        final_path = str(Path(save_path).with_suffix(ext))

        with open(final_path, "wb") as f:
            f.write(response.content)

        return final_path
    except Exception as e:
        print(f"[다운로드 실패] {url} -> {e}")
        return None


def file_to_base64(file_path: str) -> str | None:
    if not file_path or not os.path.exists(file_path):
        return None

    try:
        with open(file_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return encoded
    except Exception as e:
        print(f"[base64 변환 실패] {file_path} -> {e}")
        return None


def download_url_image_and_exchange_base64(num, url, field_name, save_dir="downloaded_images"):
    """
    1. url 파일을 로컬에 저장
    2. 저장된 파일을 base64 문자열로 변환
    3. (saved_path, base64_string) 반환
    """
    ensure_dir(save_dir)

    base_save_path = os.path.join(save_dir, f"{num}_{field_name}")
    saved_path = download_file(url, base_save_path)

    if not saved_path:
        return None, None

    base64_str = file_to_base64(saved_path)
    return saved_path, base64_str


# -----------------------------
# 값 정리
# -----------------------------
def normalize_to_string(value):
    if value is None:
        return ""

    if isinstance(value, list):
        return "|".join(map(str, value))

    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)

    return str(value)


def normalize_json_item(item: dict) -> dict:
    """
    json 데이터를 csv 한 줄 구조로 맞춤
    - 평평한 구조 / parsed 중첩 구조 둘 다 지원
    - CSV_FIELDS 칼럼만 채움
    """
    parsed = item.get("parsed") if isinstance(item.get("parsed"), dict) else item
    counts = parsed.get("counts") if isinstance(parsed.get("counts"), dict) else {}
    video = parsed.get("video") if isinstance(parsed.get("video"), dict) else {}

    normalized = {
        "num": "",
        "nickname": normalize_to_string(parsed.get("nickname")),
        "user_id": normalize_to_string(parsed.get("user_id")),
        "date": normalize_to_string(parsed.get("date")),
        "text": normalize_to_string(parsed.get("text")),
        "counts_reply": normalize_to_string(counts.get("reply")),
        "counts_retweet": normalize_to_string(counts.get("retweet")),
        "counts_like": normalize_to_string(counts.get("like")),
        "counts_view": normalize_to_string(counts.get("view")),
        "image_urls": normalize_to_string(parsed.get("image_urls")),
        "hashtags": normalize_to_string(parsed.get("hashtags")),
        "video_video_blob_url": normalize_to_string(video.get("video_blob_url")),
        "video_video_poster_url": normalize_to_string(video.get("video_poster_url")),
        "video_video_source_url": normalize_to_string(video.get("video_source_url")),
    }
    return normalized


def build_csv_duplicate_key(row: dict) -> str:
    date = str(row.get("date", "")).strip()
    user_id = str(row.get("user_id", "")).strip().lower()

    if not date or not user_id:
        return ""

    return f"{date}|{user_id}"


def get_existing_key_set(rows: list[dict]) -> set[str]:
    result = set()

    for row in rows:
        key = build_csv_duplicate_key(row)
        if key:
            result.add(key)

    return result


def get_next_num(rows: list[dict]) -> int:
    nums = []
    for row in rows:
        try:
            nums.append(int(row.get("num", 0)))
        except Exception:
            pass
    return max(nums, default=0) + 1


def convert_url_fields_to_base64(row_num: int, row_data: dict, image_save_dir="downloaded_images") -> dict:
    """
    image_urls, video_video_poster_url 만 다운로드 후 base64 변환
    profile_image_url 은 제외
    """
    converted = dict(row_data)

    image_like_fields = [
        "image_urls",
        "video_video_poster_url",
    ]

    for field in image_like_fields:
        raw_value = converted.get(field, "").strip()
        if not raw_value:
            continue

        urls = [u.strip() for u in raw_value.split("|") if u.strip()]
        base64_list = []

        for idx, url in enumerate(urls, start=1):
            sub_field_name = field if len(urls) == 1 else f"{field}_{idx}"
            _, base64_str = download_url_image_and_exchange_base64(
                num=row_num,
                url=url,
                field_name=sub_field_name,
                save_dir=image_save_dir,
            )
            if base64_str:
                base64_list.append(base64_str)

        converted[field] = "|".join(base64_list) if base64_list else ""

    return converted


# -----------------------------
# 메인 저장 함수
# -----------------------------
def save_json_to_csv(file_path, saved_file_name):
    json_data = read_json_file(file_path)

    if not isinstance(json_data, list):
        raise ValueError("JSON 파일은 리스트 형태여야 합니다.")

    existing_rows = read_existing_csv_rows(saved_file_name)
    existing_keys = get_existing_key_set(existing_rows)

    last_num = get_last_num(existing_rows)
    start_index = last_num   # num은 1부터, index는 0부터라서 그대로 다음 시작점이 됨
    next_num = last_num + 1

    added_count = 0
    skipped_count = 0
    korean_skipped_count = 0

    target_items = json_data[start_index:]

    for item in target_items:
        normalized = normalize_json_item(item)

        if not contains_korean(normalized.get("text", "")):
            korean_skipped_count += 1
            print(f"[한국어 없음 스킵] text={normalized.get('text')}")
            continue


        current_key = build_csv_duplicate_key(normalized)

        if current_key and current_key in existing_keys:
            skipped_count += 1
            print(f"[중복 스킵] key={current_key}")
            continue

        normalized["num"] = str(next_num)

        converted_row = convert_url_fields_to_base64(
            row_num=next_num,
            row_data=normalized,
            image_save_dir="downloaded_images",
        )

        append_csv_row(saved_file_name, converted_row)

        if current_key:
            existing_keys.add(current_key)

        print(f"[추가 완료] num={next_num}, key={current_key}")
        next_num += 1
        added_count += 1

    print(f"추가된 데이터: {added_count}개")
    print(f"중복으로 스킵된 데이터: {skipped_count}개")
    print(f"한국어 미포함 스킵: {korean_skipped_count}개")