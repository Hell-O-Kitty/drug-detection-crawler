from pathlib import Path
import json
import csv

from drug_detection_crawler.storage.save_tools import save_json_to_text_csv
from drug_detection_crawler.config.settings import (
    PARSED_JSON_PATH,
    TEXT_CSV_ORIGINALS_PATH,
    TEXT_CSV_PATH,
)

INPUT_JSON_PATH = PARSED_JSON_PATH
OUTPUT_CSV_PATH = TEXT_CSV_PATH
SUCCESS_ORIGINAL_JSON_PATH = TEXT_CSV_ORIGINALS_PATH


def load_json_preview(file_path: Path, preview_count: int = 2):
    if not file_path.exists():
        raise FileNotFoundError(f"JSON 파일이 없습니다: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON 파일은 리스트 형태여야 합니다.")

    print(f"[INFO] JSON 총 개수: {len(data)}")

    for idx, item in enumerate(data[:preview_count], start=1):
        print(f"\n[PREVIEW {idx}]")
        print(json.dumps(item, ensure_ascii=False, indent=2)[:1000])

    return data

def main():
    print("[STEP 1] 입력 JSON 확인")
    load_json_preview(INPUT_JSON_PATH)

    print("\n[STEP 2] JSON → CSV 저장 실행")
    save_json_to_text_csv(
        file_path=str(INPUT_JSON_PATH),
        saved_file_name=str(OUTPUT_CSV_PATH),
        source_saved_file=str(SUCCESS_ORIGINAL_JSON_PATH),
    )

    print("\n[DONE] CSV 테스트 파이프라인 완료")


if __name__ == "__main__":
    main()
