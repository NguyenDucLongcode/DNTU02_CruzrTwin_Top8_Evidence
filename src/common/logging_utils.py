import os
import json
from src.common.json_utils import clean_for_json

def ensure_dir(path: str) -> None:
    """
    Ensure the directory for the given file path exists.
    """
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)

def append_jsonl(path: str, record: dict) -> None:
    """
    Append a dictionary as a JSON line to the specified file.
    Creates parent directories if they do not exist.
    """
    ensure_dir(path)
    cleaned_record = clean_for_json(record)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(cleaned_record, ensure_ascii=False) + "\n")

def reset_file(path: str) -> None:
    """
    Reset a file by creating or clearing it, ensuring the parent directory exists.
    """
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write("")
