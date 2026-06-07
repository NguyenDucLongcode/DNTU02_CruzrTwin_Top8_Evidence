import os
import json
from datetime import datetime, timezone
from .config import LOG_DIR
from .time_utils import now_iso

def ensure_log_dir():
    """Ensures the log directory exists."""
    os.makedirs(LOG_DIR, exist_ok=True)

def validate_json_serializable(record: dict):
    """Checks if a dictionary can be serialized to JSON, raising TypeError if not."""
    json.dumps(record)

def append_jsonl(path: str, record: dict):
    """
    Appends a record to a JSONL log file.
    Ensures that parent directories are created.
    """
    validate_json_serializable(record)
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def build_base_log_context(demo_run_id: str, scenario_id: str, scenario_source: str, zone_id: str) -> dict:
    """
    Builds the default dict header structure for logs.
    """
    return {
        "demo_run_id": demo_run_id,
        "scenario_id": scenario_id,
        "scenario_source": scenario_source,
        "zone_id": zone_id,
        "timestamp": now_iso()
    }
