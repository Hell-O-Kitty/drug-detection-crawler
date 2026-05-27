import requests
import json
import os
import csv
import base64
import mimetypes
from pathlib import Path
from urllib.parse import urlparse
import re

from drug_detection_crawler.config.settings import DOWNLOADED_IMAGE_DIR
from drug_detection_crawler.config.settings import (
    MEDIA_DOWNLOAD_COLUMNS,
    MEDIA_DOWNLOAD_DIR,
    MEDIA_DOWNLOAD_ON_SAVE,
)
from drug_detection_crawler.parsers.tweet_parser import parse_tweet_html

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
    "tweet_url",
]

TEXT_CSV_FIELDS = CSV_FIELDS[:]


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


def read_json_list_file(file_path: str) -> list:
    if not os.path.exists(file_path):
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON 파일은 리스트 형태여야 합니다.")

    return data


def write_json_file(data, file_path: str) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")

    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, separators=(",", ": "))

    tmp_path.replace(path)


def delete_file(file_path: str) -> None:
    path = Path(file_path)
    if path.exists():
        path.unlink()


def read_existing_csv_rows(csv_path: str):
    if not os.path.exists(csv_path):
        return []

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def insert_csv_column(csv_path: str, column_name: str, after_column_name: str) -> None:
    path = Path(csv_path)
    if not path.exists() or path.stat().st_size == 0:
        return

    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    if not rows:
        return

    header = rows[0]
    if column_name in header or after_column_name not in header:
        return

    insert_index = header.index(after_column_name) + 1
    header.insert(insert_index, column_name)

    for row in rows[1:]:
        while len(row) < len(header) - 1:
            row.append("")
        row.insert(insert_index, "")

    tmp_path = path.with_name(f"{path.name}.tmp")
    with open(tmp_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    tmp_path.replace(path)


def ensure_text_csv_schema(csv_path: str) -> None:
    insert_csv_column(
        csv_path=csv_path,
        column_name="tweet_url",
        after_column_name="video_video_source_url",
    )


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


def get_csv_fieldnames(csv_path: str, default_fields: list[str]) -> list[str]:
    if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
        return default_fields

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return default_fields

    if "video_video_source_url" not in header:
        return default_fields

    if all(field in header for field in default_fields):
        return header

    text_field_count = len(default_fields)
    required_prefix = header[:text_field_count]

    if required_prefix == default_fields:
        return header

    return default_fields


def append_text_csv_row(csv_path: str, row: dict) -> None:
    fieldnames = get_csv_fieldnames(csv_path, TEXT_CSV_FIELDS)
    file_exists = os.path.exists(csv_path)
    normalized_row = {field: row.get(field, "") for field in fieldnames}

    with open(csv_path, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists or os.path.getsize(csv_path) == 0:
            writer.writeheader()

        writer.writerow(normalized_row)


def append_success_original_item(
    item: dict,
    csv_num: int,
    duplicate_keys: set[str],
) -> dict:
    return {
        "csv_num": csv_num,
        "duplicate_keys": sorted(duplicate_keys),
        "source_item": item,
    }

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


def get_extension_from_bytes(data: bytes) -> str:
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return ".gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return ".webp"
    return ".jpg"


def save_base64_image(value: str, save_path: str) -> str | None:
    try:
        base64_value = value.strip()

        if base64_value.startswith("data:image") and "," in base64_value:
            base64_value = base64_value.split(",", 1)[1]

        base64_value = "".join(base64_value.split())
        padding = len(base64_value) % 4
        if padding:
            base64_value += "=" * (4 - padding)

        image_bytes = base64.b64decode(base64_value, validate=True)
        final_path = str(Path(save_path).with_suffix(get_extension_from_bytes(image_bytes)))

        with open(final_path, "wb") as f:
            f.write(image_bytes)

        return final_path
    except Exception as e:
        print(f"[base64 이미지 저장 실패] {save_path} -> {e}")
        return None


def save_media_value(value: str, save_path: str) -> str | None:
    if value.startswith(("http://", "https://")):
        return download_file(value, save_path)

    if value.startswith(("blob:",)):
        return None

    return save_base64_image(value, save_path)


def download_media_files_for_row(
    row_num: int,
    row_data: dict,
    save_dir=MEDIA_DOWNLOAD_DIR,
    columns=MEDIA_DOWNLOAD_COLUMNS,
) -> tuple[int, list[str]]:
    ensure_dir(save_dir)

    saved_count = 0
    failed_columns = []

    for column_name in columns:
        raw_value = str(row_data.get(column_name, "") or "").strip()
        if not raw_value:
            continue

        values = [value.strip() for value in raw_value.split("|") if value.strip()]

        for idx, value in enumerate(values, start=1):
            file_name = (
                f"{row_num}_{column_name}"
                if len(values) == 1
                else f"{row_num}_{column_name}_{idx}"
            )
            saved_path = save_media_value(
                value=value,
                save_path=str(Path(save_dir) / file_name),
            )

            if saved_path:
                saved_count += 1
            else:
                failed_columns.append(f"{column_name}_{idx}")

    return saved_count, failed_columns


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


def download_url_image_and_exchange_base64(num, url, field_name, save_dir=DOWNLOADED_IMAGE_DIR):
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


def get_tweet_url_from_item(item: dict, parsed: dict) -> str:
    tweet_url = parsed.get("tweet_url")
    if tweet_url:
        return normalize_to_string(tweet_url)

    raw_html = item.get("raw_html")
    if not raw_html:
        return ""

    parsed_from_html = parse_tweet_html(raw_html)
    return normalize_to_string(parsed_from_html.get("tweet_url"))


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
        "tweet_url": get_tweet_url_from_item(item, parsed),
    }
    return normalized


def normalize_duplicate_value(value) -> str:
    return " ".join(str(value or "").strip().lower().split())


def build_csv_duplicate_key(row: dict) -> str:
    date = str(row.get("date", "")).strip()
    user_id = str(row.get("user_id", "")).strip().lower()

    if not date or not user_id:
        return ""

    return f"{date}|{user_id}"


def build_csv_duplicate_keys(row: dict) -> set[str]:
    keys = set()

    date = normalize_duplicate_value(row.get("date"))
    user_id = normalize_duplicate_value(row.get("user_id"))
    text = normalize_duplicate_value(row.get("text"))

    if date and user_id:
        keys.add(f"date_user:{date}|{user_id}")

    if user_id and text:
        keys.add(f"user_text:{user_id}|{text}")

    if date and text:
        keys.add(f"date_text:{date}|{text}")

    return keys


def get_existing_key_set(rows: list[dict]) -> set[str]:
    result = set()

    for row in rows:
        result.update(build_csv_duplicate_keys(row))

    return result


def get_duplicate_key_to_csv_num(rows: list[dict]) -> dict[str, int]:
    result = {}

    for row in rows:
        if not normalize_duplicate_value(row.get("tweet_url")):
            continue

        try:
            csv_num = int(row.get("num", 0))
        except (TypeError, ValueError):
            continue

        for key in build_csv_duplicate_keys(row):
            result.setdefault(key, csv_num)

    return result


def get_next_num(rows: list[dict]) -> int:
    nums = []
    for row in rows:
        try:
            nums.append(int(row.get("num", 0)))
        except Exception:
            pass
    return max(nums, default=0) + 1


def convert_url_fields_to_base64(row_num: int, row_data: dict, image_save_dir=DOWNLOADED_IMAGE_DIR) -> dict:
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


        current_keys = build_csv_duplicate_keys(normalized)

        if current_keys and current_keys.intersection(existing_keys):
            skipped_count += 1
            print(f"[중복 스킵] key={sorted(current_keys)[0]}")
            continue

        normalized["num"] = str(next_num)

        converted_row = convert_url_fields_to_base64(
            row_num=next_num,
            row_data=normalized,
            image_save_dir=DOWNLOADED_IMAGE_DIR,
        )

        append_csv_row(saved_file_name, converted_row)

        existing_keys.update(current_keys)

        print(f"[추가 완료] num={next_num}")
        next_num += 1
        added_count += 1

    print(f"추가된 데이터: {added_count}개")
    print(f"중복으로 스킵된 데이터: {skipped_count}개")
    print(f"한국어 미포함 스킵: {korean_skipped_count}개")


def save_json_to_text_csv(file_path, saved_file_name, source_saved_file=None):
    json_data = read_json_file(file_path)

    if not isinstance(json_data, list):
        raise ValueError("JSON 파일은 리스트 형태여야 합니다.")

    ensure_text_csv_schema(saved_file_name)
    existing_rows = read_existing_csv_rows(saved_file_name)
    existing_keys = get_existing_key_set(existing_rows)
    duplicate_key_to_csv_num = get_duplicate_key_to_csv_num(existing_rows)
    next_num = get_next_num(existing_rows)

    added_count = 0
    skipped_count = 0
    korean_skipped_count = 0
    no_key_count = 0
    original_items = read_json_list_file(source_saved_file) if source_saved_file else []
    original_csv_nums = {
        int(item.get("csv_num", 0))
        for item in original_items
        if str(item.get("csv_num", "")).isdigit()
    }
    original_added_count = 0
    original_backfill_count = 0

    for item in json_data:
        normalized = normalize_json_item(item)

        if not contains_korean(normalized.get("text", "")):
            korean_skipped_count += 1
            continue

        current_keys = build_csv_duplicate_keys(normalized)

        if current_keys and current_keys.intersection(existing_keys):
            if source_saved_file:
                matched_csv_nums = {
                    duplicate_key_to_csv_num[key]
                    for key in current_keys
                    if key in duplicate_key_to_csv_num
                }
                missing_csv_nums = sorted(matched_csv_nums - original_csv_nums)

                if missing_csv_nums:
                    csv_num = missing_csv_nums[0]
                    original_items.append(append_success_original_item(
                        item=item,
                        csv_num=csv_num,
                        duplicate_keys=current_keys,
                    ))
                    original_csv_nums.add(csv_num)
                    original_added_count += 1
                    original_backfill_count += 1

            skipped_count += 1
            continue

        if not current_keys:
            no_key_count += 1

        normalized["num"] = str(next_num)
        append_text_csv_row(saved_file_name, normalized)

        if MEDIA_DOWNLOAD_ON_SAVE:
            saved_media_count, failed_media_columns = download_media_files_for_row(
                row_num=next_num,
                row_data=normalized,
                save_dir=MEDIA_DOWNLOAD_DIR,
            )
            if saved_media_count or failed_media_columns:
                print(
                    f"[이미지 저장] num={next_num}, "
                    f"saved={saved_media_count}, failed={len(failed_media_columns)}"
                )

        if source_saved_file:
            original_items.append(append_success_original_item(
                item=item,
                csv_num=next_num,
                duplicate_keys=current_keys,
            ))
            original_csv_nums.add(next_num)
            original_added_count += 1

        existing_keys.update(current_keys)
        next_num += 1
        added_count += 1

    if source_saved_file and original_added_count:
        write_json_file(original_items, source_saved_file)

    delete_file(file_path)

    print("[DONE]")
    print(f"추가된 데이터: {added_count}개")
    print(f"중복으로 스킵된 데이터: {skipped_count}개")
    print(f"한국어 미포함 스킵: {korean_skipped_count}개")
    print(f"중복 키 없이 추가된 데이터: {no_key_count}개")
    print(f"원본 저장: {original_added_count}개")
    print(f"누락 원본 복구: {original_backfill_count}개")
    print("입력 JSON 중간 파일 삭제 완료")
