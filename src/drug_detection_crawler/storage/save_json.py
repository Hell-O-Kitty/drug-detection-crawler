import json
from pathlib import Path


def load_json(file_path: Path) -> list:
    if not file_path.exists():
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data, file_path: Path):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = file_path.with_name(f"{file_path.name}.tmp")

    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=1,
            separators=(",", ": ")
        )

    tmp_path.replace(file_path)


def delete_json(file_path: Path):
    if file_path.exists():
        file_path.unlink()
