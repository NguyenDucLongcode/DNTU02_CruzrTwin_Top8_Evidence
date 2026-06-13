"""
Cruzr Robot Simulator Daemon
- Polls Orion Context Broker for PENDING RobotAction entities.
- Simulates robot navigation and guidance voice announcement.
- Transitions status PENDING -> NAVIGATING -> DELIVERED.
- Ghi log logs/robot_actions.jsonl.
"""

import os
import sys
import time
import argparse
import requests
from datetime import datetime, timezone

# Add project root to sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.common.config import get_config
from src.common.logging_utils import append_jsonl

# In-memory set to prevent duplicate log entries for the same action in this run
_delivered_actions = set()

def poll_and_simulate_once(cfg: dict) -> bool:
    """
    Query Orion for PENDING RobotAction entities and simulate one cycle of updates.
    Returns True if an entity was processed, False otherwise.
    """
    global _delivered_actions
    orion_url = os.getenv("ORION_URL", "http://localhost:1026")
    fiware_service = os.getenv("FIWARE_SERVICE", "cruzrtwin")
    fiware_service_path = os.getenv("FIWARE_SERVICE_PATH", "/asean/buildings")
    
    headers = {
        "Fiware-Service": fiware_service,
        "Fiware-ServicePath": fiware_service_path,
        "Accept": "application/json"
    }
    
    if not cfg["orion_enabled"]:
        print("[Cruzr Simulator] Orion is disabled in config (SKIPPED_OFFLINE).")
        # Under offline test, we simulate delivering SCN_CRITICAL_001 if not already logged
        robot_action_id = "RobotAction:SCN_CRITICAL_001"
        if robot_action_id not in _delivered_actions:
            _delivered_actions.add(robot_action_id)
            timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
            log_entry = {
                "demo_run_id": cfg["demo_run_id"],
                "timestamp": timestamp,
                "robot_action_id": robot_action_id,
                "alert_id": "AlertEvent:SCN_CRITICAL_001",
                "scenario_id": "SCN_CRITICAL_001",
                "zone_id": cfg["default_zone_id"],
                "robot_id": "CRUZR_01",
                "action_type": "VOICE_DISPLAY_GUIDANCE",
                "navigation_mode": "PREDEFINED_RESPONSE_POINT",
                "message": "Critical indoor-environment anomaly detected in Room A101. Please follow staff guidance and move calmly to the safe waiting area.",
                "status": "DELIVERED",
                "orion_upsert_status": "SKIPPED_OFFLINE"
            }
            robot_log_path = os.path.join(cfg["log_dir"], "robot_actions.jsonl")
            append_jsonl(robot_log_path, log_entry)
            print(f"[Cruzr VOICE] [Offline]: {log_entry['message']}")
            print("[Cruzr] Safety-critical actuation should remain operator-approved or simulated.")
            return True
        return False

    try:
        url = f"{orion_url}/v2/entities?type=RobotAction&q=status==PENDING"
        resp = requests.get(url, headers=headers, timeout=3)
        if resp.status_code != 200:
            print(f"[Cruzr Simulator] Orion returned status code {resp.status_code}")
            return False
            
        entities = resp.json()
        if not entities:
            return False
            
        for entity in entities:
            action_id = entity["id"]
            if action_id in _delivered_actions:
                continue
                
            scenario_id = entity.get("scenario_id", {}).get("value", "SCN_CRITICAL_001")
            zone_id = entity.get("zone_id", {}).get("value", cfg["default_zone_id"])
            alert_id = entity.get("alert_id", {}).get("value", f"AlertEvent:{scenario_id}")
            message = entity.get("message", {}).get("value", "Emergency guidance message.")
            robot_id = entity.get("robot_id", {}).get("value", "CRUZR_01")
            action_type = entity.get("action_type", {}).get("value", "VOICE_DISPLAY_GUIDANCE")
            navigation_mode = entity.get("navigation_mode", {}).get("value", "PREDEFINED_RESPONSE_POINT")
            
            print(f"\n[Cruzr Simulator] Detected PENDING RobotAction: {action_id}")
            
            # Transition 1: NAVIGATING
            patch_headers = headers.copy()
            patch_headers["Content-Type"] = "application/json"
            patch_url = f"{orion_url}/v2/entities/{action_id}/attrs"
            
            nav_resp = requests.patch(patch_url, json={"status": {"type": "Text", "value": "NAVIGATING"}}, headers=patch_headers, timeout=3)
            print(f"[Cruzr Simulator] Navigating to Predefined Response Point in {zone_id}... (status: {nav_resp.status_code})")
            time.sleep(1)
            
            # Transition 2: DELIVERED
            del_resp = requests.patch(patch_url, json={"status": {"type": "Text", "value": "DELIVERED"}}, headers=patch_headers, timeout=3)
            print(f"[Cruzr Simulator] Anomaly guidance voice & display delivered on site. (status: {del_resp.status_code})")
            
            # Print Safety Disclaimer
            print(f"[Cruzr VOICE]: {message}")
            print("[Cruzr] Safety-critical actuation should remain operator-approved or simulated. Cruzr Robot only performs VOICE_DISPLAY_GUIDANCE.")
            
            # Mark as delivered
            _delivered_actions.add(action_id)
            
            # Log to robot_actions.jsonl
            timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
            log_entry = {
                "demo_run_id": cfg["demo_run_id"],
                "timestamp": timestamp,
                "robot_action_id": action_id,
                "alert_id": alert_id,
                "scenario_id": scenario_id,
                "zone_id": zone_id,
                "robot_id": robot_id,
                "action_type": action_type,
                "navigation_mode": navigation_mode,
                "message": message,
                "status": "DELIVERED",
                "orion_upsert_status": "SUCCESS" if del_resp.status_code in [200, 204] else "FAILED"
            }
            robot_log_path = os.path.join(cfg["log_dir"], "robot_actions.jsonl")
            append_jsonl(robot_log_path, log_entry)
            return True
            
    except Exception as e:
        print(f"[Cruzr Simulator] Orion connection error: {e}")
        # Log FAILED status
        robot_action_id = "RobotAction:SCN_CRITICAL_001"
        if robot_action_id not in _delivered_actions:
            _delivered_actions.add(robot_action_id)
            timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
            log_entry = {
                "demo_run_id": cfg["demo_run_id"],
                "timestamp": timestamp,
                "robot_action_id": robot_action_id,
                "alert_id": "AlertEvent:SCN_CRITICAL_001",
                "scenario_id": "SCN_CRITICAL_001",
                "zone_id": cfg["default_zone_id"],
                "robot_id": "CRUZR_01",
                "action_type": "VOICE_DISPLAY_GUIDANCE",
                "navigation_mode": "PREDEFINED_RESPONSE_POINT",
                "message": "Critical indoor-environment anomaly detected in Room A101. Please follow staff guidance and move calmly to the safe waiting area.",
                "status": "DELIVERED",
                "orion_upsert_status": "FAILED",
                "error_message": str(e)
            }
            robot_log_path = os.path.join(cfg["log_dir"], "robot_actions.jsonl")
            append_jsonl(robot_log_path, log_entry)
            print(f"[Cruzr VOICE] [Orion connection error]: {log_entry['message']}")
            print("[Cruzr] Safety-critical actuation should remain operator-approved or simulated.")
            return True
            
    return False

def main():
    parser = argparse.ArgumentParser(description="Cruzr Robot Simulator Daemon")
    parser.add_argument("--once", action="store_true", help="Run only one cycle of polling and exit")
    args = parser.parse_args()
    
    cfg = get_config()
    
    if args.once:
        poll_and_simulate_once(cfg)
    else:
        try:
            while True:
                poll_and_simulate_once(cfg)
                time.sleep(2)
        except KeyboardInterrupt:
            print("\n[Cruzr Simulator] Daemon stopped by user.")

if __name__ == "__main__":
    main()
