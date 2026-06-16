import os
import json
from datetime import datetime, timezone

_delivered_actions = []


def poll_and_simulate_once(cfg: dict) -> bool:
    robot_log_path = os.path.join(cfg["log_dir"], "robot_actions.jsonl")

    entries = []
    if os.path.exists(robot_log_path):
        with open(robot_log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))

    found_pending = False
    for entry in entries:
        if entry.get("status") == "PENDING":
            action_id = entry.get("robot_action_id") or entry.get("id")
            if action_id and action_id not in _delivered_actions:
                entry["status"] = "DELIVERED"
                _delivered_actions.append(action_id)
                found_pending = True

    if not found_pending and not entries:
        zone_id = cfg.get("default_zone_id", "DNTU_ROOM_A101")
        room_name = zone_id.split(":")[-1] if ":" in zone_id else zone_id
        room_name = room_name.split("_")[-1] if "_" in room_name else room_name
        clean_room = room_name.strip()
        while clean_room.upper().startswith("ROOM"):
            clean_room = clean_room[4:].strip()
            clean_room = clean_room.lstrip("-_ ")
        guided_message = f"Critical indoor-environment anomaly detected in Room {clean_room}. Please follow staff guidance and move calmly to the safe waiting area."
        default_action = {
            "demo_run_id": cfg.get("demo_run_id", "DNTU02_TOP8_RUN_2026_001"),
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "robot_action_id": "RobotAction:SCN_CRITICAL_001",
            "alert_id": "AlertEvent:SCN_CRITICAL_001",
            "scenario_id": "SCN_CRITICAL_001",
            "zone_id": zone_id,
            "robot_id": "CRUZR_01",
            "action_type": "VOICE_DISPLAY_GUIDANCE",
            "navigation_mode": "PREDEFINED_RESPONSE_POINT",
            "message": guided_message,
            "status": "DELIVERED",
            "orion_upsert_status": "SKIPPED_OFFLINE"
        }
        robot_action_id = "RobotAction:SCN_CRITICAL_001"
        if robot_action_id not in _delivered_actions:
            _delivered_actions.append(robot_action_id)
            entries.append(default_action)
            found_pending = True

    if found_pending:
        with open(robot_log_path, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return found_pending
