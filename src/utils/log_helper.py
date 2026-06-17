import os
import json
import sys
from datetime import datetime, timezone


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)
from src.fiware import get_room_state

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def write_orion_state_log(zone_id: str,):
    """
    Ghi log Orion state: Room, Devices, AlertEvent (AI), RobotAction
    Theo file Word 4.2
    """
    log_file = "logs/orion_state.jsonl"
    os.makedirs("logs", exist_ok=True)
    
    # Lấy Room entity
    room = get_room_state(zone_id) or {}

    # Lấy tất cả Device entities
    device_ids = room.get("device_ids", [])
    
    
    # Log đầy đủ
    log_entry = {
        "timestamp": _utc_now(),
        "demo_run_id": os.getenv("DEMO_RUN_ID", "DNTU02_TOP8_RUN_2026_001"),
        "room": zone_id,
        "devices": device_ids,
    }
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    print(f"   📝 Orion state logged: {log_file}")