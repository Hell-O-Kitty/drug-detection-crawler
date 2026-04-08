import json
from pathlib import Path


def load_json(file_path: Path) -> list:
    if not file_path.exists():
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data, file_path: Path):
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=1,
            separators=(",", ": ")
        )