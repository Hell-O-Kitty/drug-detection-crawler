import argparse
import base64
import binascii
import csv
import json
import mimetypes
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

from drug_detection_crawler.config.settings import (
    MEDIA_DOWNLOAD_COLUMNS,
    MEDIA_DOWNLOAD_CSV_PATH,
    MEDIA_DOWNLOAD_DIR,
    MEDIA_DOWNLOAD_END_ID,
    MEDIA_DOWNLOAD_RETRY_COUNT,
    MEDIA_DOWNLOAD_START_ID,
    MEDIA_DOWNLOAD_TIMEOUT,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download image URLs from x_crawling_drugs_text.csv.",
    )
    parser.add_argument(
        "--start-id",
        type=int,
        default=None,
        help="First num id to download.",
    )
    parser.add_argument(
        "--end-id",
        type=int,
        default=None,
        help="Last num id to download.",
    )
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=MEDIA_DOWNLOAD_CSV_PATH,
        help="CSV file path.",
    )
    parser.add_argument(
        "--save-dir",
        type=Path,
        default=MEDIA_DOWNLOAD_DIR,
        help="Directory to save downloaded images.",
    )
    return parser.parse_args()


def input_int(prompt: str, default: int | None) -> int | None:
    default_text = "" if default is None else str(default)
    value = input(f"{prompt} [{default_text}]: ").strip()

    if not value:
        return default

    try:
        return int(value)
    except ValueError:
        print("숫자만 입력해주세요.")
        return input_int(prompt, default)


def resolve_download_range(args: argparse.Namespace) -> tuple[int, int | None]:
    start_id = args.start_id
    end_id = args.end_id

    if start_id is None:
        start_id = input_int("다운로드 시작 id", MEDIA_DOWNLOAD_START_ID)

    if end_id is None:
        end_id = input_int("다운로드 종료 id (전체는 Enter)", MEDIA_DOWNLOAD_END_ID)

    return start_id or MEDIA_DOWNLOAD_START_ID, end_id


def parse_id(value: str) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def is_in_download_range(row_id: int, start_id: int, end_id: int | None) -> bool:
    if row_id < start_id:
        return False

    if end_id is not None and row_id > end_id:
        return False

    return True


def parse_urls(raw_value: str) -> list[str]:
    value = str(raw_value or "").strip()
    if not value:
        return []

    if value.startswith("["):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            parsed = None

        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]

    return [url.strip() for url in re.split(r"\s*\|\s*", value) if url.strip()]


def get_extension(url: str, response: requests.Response) -> str:
    url_ext = Path(urlparse(url).path).suffix.lower()
    if url_ext:
        return url_ext

    content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
    guessed_ext = mimetypes.guess_extension(content_type)
    return guessed_ext or ".bin"


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


def decode_base64_image(value: str) -> bytes:
    base64_value = value.strip()

    if base64_value.startswith("data:image") and "," in base64_value:
        base64_value = base64_value.split(",", 1)[1]

    base64_value = "".join(base64_value.split())
    padding = len(base64_value) % 4
    if padding:
        base64_value += "=" * (4 - padding)

    return base64.b64decode(base64_value, validate=True)


def build_file_stem(row_id: int, column_name: str, url_count: int, url_index: int) -> str:
    if url_count == 1:
        return f"{row_id}_{column_name}"

    return f"{row_id}_{column_name}_{url_index}"


def download_url(url: str, save_stem: Path) -> Path:
    response = requests.get(url, timeout=MEDIA_DOWNLOAD_TIMEOUT)
    response.raise_for_status()

    save_path = save_stem.with_suffix(get_extension(url, response))
    save_path.write_bytes(response.content)
    return save_path


def save_base64_image(value: str, save_stem: Path) -> Path:
    image_bytes = decode_base64_image(value)
    save_path = save_stem.with_suffix(get_extension_from_bytes(image_bytes))
    save_path.write_bytes(image_bytes)
    return save_path


def download_with_retry(url: str, save_stem: Path) -> tuple[Path | None, str | None]:
    if not url.startswith(("http://", "https://")):
        try:
            return save_base64_image(url, save_stem), None
        except (binascii.Error, ValueError) as exc:
            return None, f"Not downloadable URL or base64 image: {exc}"

    for attempt in range(1, MEDIA_DOWNLOAD_RETRY_COUNT + 1):
        try:
            return download_url(url, save_stem), None
        except requests.RequestException as exc:
            if attempt == MEDIA_DOWNLOAD_RETRY_COUNT:
                return None, str(exc)

            time.sleep(min(attempt, 5))

    return None, "Unknown error"


def iter_target_rows(csv_path: Path, start_id: int, end_id: int | None):
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            row_id = parse_id(row.get("num", ""))
            if row_id is None or not is_in_download_range(row_id, start_id, end_id):
                continue

            yield row_id, row


def count_target_urls(csv_path: Path, start_id: int, end_id: int | None) -> int:
    total_count = 0

    for _, row in iter_target_rows(csv_path, start_id, end_id):
        for column_name in MEDIA_DOWNLOAD_COLUMNS:
            total_count += len(parse_urls(row.get(column_name, "")))

    return total_count


def print_progress(done_count: int, total_count: int, success_count: int, fail_count: int) -> None:
    if total_count:
        print(
            f"[PROGRESS] {done_count}/{total_count} "
            f"(success={success_count}, fail={fail_count})"
        )
    else:
        print("[PROGRESS] No image URLs found.")


def format_failed_summary(failed_results: list[dict]) -> str:
    if not failed_results:
        return "Failed ids: none\n"

    grouped: dict[int, int] = {}
    details = []

    for item in failed_results:
        row_id = item["row_id"]
        grouped[row_id] = grouped.get(row_id, 0) + 1
        details.append(
            f"id={row_id}, column={item['column_name']}, index={item['url_index']}, error={item['error']}"
        )

    id_summary = ", ".join(
        f"{row_id}({fail_count})" for row_id, fail_count in sorted(grouped.items())
    )
    return f"Failed ids: {id_summary}\nFailed details:\n" + "\n".join(details) + "\n"


def save_failed_summary(save_dir: Path, failed_results: list[dict]) -> Path:
    failed_list_path = save_dir / "failed_download_list.txt"
    failed_list_path.write_text(format_failed_summary(failed_results), encoding="utf-8")
    return failed_list_path


def download_media_from_csv(
    csv_path: Path,
    save_dir: Path,
    start_id: int,
    end_id: int | None,
) -> None:
    save_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    failed_results = []

    print(f"[INFO] csv_path={csv_path}")
    print(f"[INFO] save_dir={save_dir}")
    print(f"[INFO] range={start_id}~{end_id if end_id is not None else 'end'}")
    total_count = count_target_urls(csv_path, start_id, end_id)
    done_count = 0
    print(f"[INFO] target image urls={total_count}")
    print_progress(done_count, total_count, success_count, len(failed_results))

    for row_id, row in iter_target_rows(csv_path, start_id, end_id):
        for column_name in MEDIA_DOWNLOAD_COLUMNS:
            urls = parse_urls(row.get(column_name, ""))

            for index, url in enumerate(urls, start=1):
                file_stem = build_file_stem(
                    row_id=row_id,
                    column_name=column_name,
                    url_count=len(urls),
                    url_index=index,
                )
                saved_path, error = download_with_retry(
                    url=url,
                    save_stem=save_dir / file_stem,
                )

                if saved_path:
                    success_count += 1
                else:
                    failed_results.append(
                        {
                            "row_id": row_id,
                            "column_name": column_name,
                            "url_index": index,
                            "error": error,
                        }
                    )

                done_count += 1
                print_progress(done_count, total_count, success_count, len(failed_results))

    print("[DONE]")
    print(f"Downloaded files: {success_count}")
    print(f"Failed downloads: {len(failed_results)}")

    failed_list_path = save_failed_summary(save_dir, failed_results)
    print(f"Failed list saved: {failed_list_path}")


def main() -> None:
    args = parse_args()
    start_id, end_id = resolve_download_range(args)

    download_media_from_csv(
        csv_path=args.csv_path,
        save_dir=args.save_dir,
        start_id=start_id,
        end_id=end_id,
    )


if __name__ == "__main__":
    main()
