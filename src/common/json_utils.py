import json
import os
from typing import Any, List, Optional

def load_json(path: str) -> Optional[Any]:
    """Safely loads a JSON file."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def write_json(path: str, data: Any, indent: int = 2) -> bool:
    """Safely writes data to a JSON file, creating parent directories."""
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except Exception:
        return False

def load_jsonl(path: str) -> List[dict]:
    """Safely loads a JSONL file."""
    if not os.path.exists(path):
        return []
    records = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    try:
                        records.append(json.loads(line_str))
                    except json.JSONDecodeError:
                        continue
    except Exception:
        pass
    return records
