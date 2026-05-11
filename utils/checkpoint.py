import json
import os
from pathlib import Path


def save_checkpoint(data: dict, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_checkpoint(path: str) -> dict | None:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def checkpoint_or_run(path: str, fn, *args, **kwargs) -> dict:
    existing = load_checkpoint(path)
    if existing is not None:
        print(f"  [checkpoint] cargado desde {path}")
        return existing
    result = fn(*args, **kwargs)
    save_checkpoint(result, path)
    return result
