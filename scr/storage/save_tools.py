import requests
import json
import os

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

def download_image(url, save_path):
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()

        with open(save_path, "wb") as f:
            f.write(res.content)

        print(f"Saved: {save_path}")

    except Exception as e:
        print(f"Failed: {url} -> {e}")

import json
import os

def save_to_json(data, path="result.json"):
    # 기존 데이터 불러오기
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            existing_data = []
    else:
        existing_data = []

    # 리스트 형태로 맞추기
    if not isinstance(existing_data, list):
        existing_data = [existing_data]

    if isinstance(data, list):
        existing_data.extend(data)
    else:
        existing_data.append(data)

    # 다시 저장
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)

    print(f"{len(existing_data)}개 데이터 저장 완료")

import os
import csv
import json
import base64
import mimetypes
from pathlib import Path
from urllib.parse import urlparse

import requests


CSV_FIELDS = [
    "num",
    "nickname",
    "user_id",
    "profile_image_url",
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


def download_image(url: str, save_path: str, timeout: int = 15) -> str | None:
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
    1. url 이미지를 로컬에 저장
    2. 저장된 파일을 base64 문자열로 변환
    3. (saved_path, base64_string) 반환
    """
    ensure_dir(save_dir)

    base_save_path = os.path.join(save_dir, f"{num}_{field_name}")
    saved_path = download_image(url, base_save_path)

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
        # 리스트는 | 로 이어붙여 저장
        return "|".join(map(str, value))

    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)

    return str(value)


def normalize_json_item(item: dict) -> dict:
    """
    json 데이터를 csv 한 줄 구조로 맞춤
    json에는 num이 없으므로 여기서는 제외하고 나중에 채움
    """
    normalized = {
        "num": "",
        "nickname": normalize_to_string(item.get("nickname")),
        "user_id": normalize_to_string(item.get("user_id")),
        "profile_image_url": normalize_to_string(item.get("profile_image_url")),
        "date": normalize_to_string(item.get("date")),
        "text": normalize_to_string(item.get("text")),
        "counts_reply": normalize_to_string(item.get("counts_reply")),
        "counts_retweet": normalize_to_string(item.get("counts_retweet")),
        "counts_like": normalize_to_string(item.get("counts_like")),
        "counts_view": normalize_to_string(item.get("counts_view")),
        "image_urls": normalize_to_string(item.get("image_urls")),
        "hashtags": normalize_to_string(item.get("hashtags")),
        "video_video_blob_url": normalize_to_string(item.get("video_video_blob_url")),
        "video_video_poster_url": normalize_to_string(item.get("video_video_poster_url")),
        "video_video_source_url": normalize_to_string(item.get("video_video_source_url")),
    }
    return normalized


def get_existing_date_set(rows: list[dict]) -> set[str]:
    return {str(row.get("date", "")).strip() for row in rows if row.get("date")}


def get_next_num(rows: list[dict]) -> int:
    nums = []
    for row in rows:
        try:
            nums.append(int(row.get("num", 0)))
        except:
            pass
    return max(nums, default=0) + 1


def convert_url_fields_to_base64(row_num: int, row_data: dict, image_save_dir="downloaded_images") -> dict:
    """
    URL 필드들 중 이미지 성격인 것만 다운로드 후 base64로 변환
    profile_image_url, image_urls, video_video_poster_url 대상으로 처리
    """
    converted = dict(row_data)

    image_like_fields = [
        "profile_image_url",
        "image_urls",
        "video_video_poster_url",
    ]

    for field in image_like_fields:
        raw_value = converted.get(field, "").strip()
        if not raw_value:
            continue

        # image_urls는 여러 개일 수 있으니 | 기준 분리
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
    """
    1. json 파일을 입력 받고 순회
    2. csv의 date 열과 비교하여 중복 확인
    3. 중복이 아니면 새 row 번호(num) 부여
    4. 이미지 url들을 다운로드해서 {row}_{field명} 형식으로 저장
    5. csv에는 해당 url 대신 base64 문자열 저장
    """
    json_data = read_json_file(file_path)

    if not isinstance(json_data, list):
        raise ValueError("JSON 파일은 리스트 형태여야 합니다.")

    existing_rows = read_existing_csv_rows(saved_file_name)
    existing_dates = get_existing_date_set(existing_rows)
    next_num = get_next_num(existing_rows)

    added_count = 0
    skipped_count = 0

    for item in json_data:
        normalized = normalize_json_item(item)
        current_date = normalized.get("date", "").strip()

        # date 기준 중복 체크
        if current_date and current_date in existing_dates:
            skipped_count += 1
            print(f"[중복 스킵] date={current_date}")
            continue

        normalized["num"] = str(next_num)

        # URL -> base64 치환
        converted_row = convert_url_fields_to_base64(
            row_num=next_num,
            row_data=normalized,
            image_save_dir="downloaded_images",
        )

        append_csv_row(saved_file_name, converted_row)

        if current_date:
            existing_dates.add(current_date)

        print(f"[추가 완료] num={next_num}, date={current_date}")
        next_num += 1
        added_count += 1

    print(f"추가된 데이터: {added_count}개")
    print(f"중복으로 스킵된 데이터: {skipped_count}개")