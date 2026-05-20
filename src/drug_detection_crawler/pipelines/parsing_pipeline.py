import json
from pathlib import Path

from drug_detection_crawler.parsers.tweet_parser import parse_collected_item
from drug_detection_crawler.config.settings import RAW_JSON_PATH, PARSED_JSON_PATH
from drug_detection_crawler.storage.save_json import delete_json, load_json, save_json

RAW_FILE_PATH = RAW_JSON_PATH
OUTPUT_FILE_PATH = PARSED_JSON_PATH


def normalize_key(value) -> str:
    return str(value or "").strip().lower()


def rebuild_raw_item_keys(raw_data: list[dict]) -> tuple[list[dict], int]:
    updated_count = 0
    rebuilt_raw = []

    for item in raw_data:
        parsed_item = parse_collected_item(item)

        if not parsed_item:
            rebuilt_raw.append(item)
            continue

        new_key = normalize_key(parsed_item.get("item_key"))
        old_key = normalize_key(item.get("item_key"))

        if new_key and old_key != new_key:
            item["item_key"] = new_key
            updated_count += 1
        elif new_key:
            item["item_key"] = new_key

        rebuilt_raw.append(item)

    return rebuilt_raw, updated_count


def run_parse_and_cleanup():
    raw_data = load_json(RAW_FILE_PATH)
    processed_data = load_json(OUTPUT_FILE_PATH)

    # 1) raw 안의 기존 item_key를 전부 date|user_id 기준으로 재구성
    raw_data, rebuilt_count = rebuild_raw_item_keys(raw_data)

    # 재구성된 raw를 먼저 저장
    save_json(raw_data, RAW_FILE_PATH)

    # 2) output 기준 key 목록 생성
    processed_keys = {
        normalize_key(item.get("item_key"))
        for item in processed_data
        if normalize_key(item.get("item_key"))
    }

    new_processed = processed_data[:]
    new_count = 0
    skip_count = 0
    fail_count = 0

    for item in raw_data:
        item_key = normalize_key(item.get("item_key"))

        # raw에 key가 없으면 다시 파싱 시도
        if not item_key:
            parsed_item = parse_collected_item(item)
            if not parsed_item:
                fail_count += 1
                continue

            item_key = normalize_key(parsed_item.get("item_key"))
            if not item_key:
                fail_count += 1
                continue
        else:
            parsed_item = parse_collected_item(item)
            if not parsed_item:
                fail_count += 1
                continue

            parsed_item["item_key"] = item_key

        # 3) tweet_datas.json 안에 있으면 추가하지 않고 다음 토큰
        if item_key in processed_keys:
            skip_count += 1
            continue

        new_processed.append(parsed_item)
        processed_keys.add(item_key)
        new_count += 1

    save_json(new_processed, OUTPUT_FILE_PATH)
    delete_json(RAW_FILE_PATH)

    print("[DONE]")
    print(f" - raw item_key 재구성: {rebuilt_count}")
    print(f" - 기존 OUTPUT: {len(processed_data)}")
    print(f" - 추가: {new_count}")
    print(f" - 중복 스킵: {skip_count}")
    print(f" - 파싱 실패 삭제: {fail_count}")
    print(" - raw 중간 파일 삭제 완료")
    print(f" - 최종 OUTPUT: {len(new_processed)}")


def main():
    run_parse_and_cleanup()


if __name__ == "__main__":
    main()
