import json
import csv
import os
import sys


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)



def normalize_data(data):
    """
    JSON이
    - list[dict]
    - dict
    형태일 때 CSV 변환용 리스트로 맞춤
    """
    if isinstance(data, list):
        if not data:
            raise ValueError("JSON 리스트가 비어 있습니다.")
        if not isinstance(data[0], dict):
            raise ValueError("JSON 리스트의 원소가 dict 형태가 아닙니다.")
        return data

    if isinstance(data, dict):
        return [data]

    raise ValueError("지원하지 않는 JSON 구조입니다.")



def flatten_dict(data: dict, parent_key: str = "", sep: str = "_") -> dict:
    """
    중첩 dict를 1차원으로 펼침.
    예:
    {"counts": {"reply": 0}} -> {"counts_reply": 0}
    """
    items = {}

    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key

        if isinstance(value, dict):
            items.update(flatten_dict(value, new_key, sep=sep))
        elif isinstance(value, list):
            # 리스트는 CSV 한 칸에 문자열로 저장
            if all(not isinstance(x, (dict, list)) for x in value):
                items[new_key] = ", ".join(map(str, value))
            else:
                items[new_key] = json.dumps(value, ensure_ascii=False)
        else:
            items[new_key] = value

    return items



def collect_fieldnames(rows: list[dict]) -> list[str]:
    """
    모든 행의 key를 합쳐서 CSV fieldnames 생성
    첫 번째 데이터만 기준으로 삼으면 나중에 빠지는 필드가 있을 수 있어서
    전체를 한 번 훑음
    """
    fieldnames = []
    seen = set()

    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)

    return fieldnames



def clean_value(value):
    """
    CSV 저장 시 엑셀에서 문제를 일으킬 수 있는 값 정리
    - 줄바꿈 제거
    - None -> 빈 문자열
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value.replace("\r", " ").replace("\n", " ")
    return value



def save_csv(rows: list[dict], csv_path: str, fieldnames: list[str]):
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()

        for row in rows:
            normalized_row = {
                field: clean_value(row.get(field, "")) for field in fieldnames
            }
            writer.writerow(normalized_row)



def json_to_csv(json_path: str, csv_path: str | None = None):
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {json_path}")

    data = load_json(json_path)
    raw_rows = normalize_data(data)

    flattened_rows = [flatten_dict(row) for row in raw_rows]
    fieldnames = collect_fieldnames(flattened_rows)

    print("감지된 field:")
    for field in fieldnames:
        print(f"- {field}")

    if csv_path is None:
        base_name = os.path.splitext(json_path)[0]
        csv_path = f"{base_name}.csv"

    save_csv(flattened_rows, csv_path, fieldnames)
    print(f"\nCSV 저장 완료: {csv_path}")



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법:")
        print("python json_to_csv.py input.json [output.csv]")
        sys.exit(1)

    input_json = sys.argv[1]
    output_csv = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        json_to_csv(input_json, output_csv)
    except Exception as e:
        print(f"에러 발생: {e}")
        sys.exit(1)
