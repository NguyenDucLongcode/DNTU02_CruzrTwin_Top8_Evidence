import os
import sys
import json

# Add project root to path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from src.common.config import LOG_DIR

AI_LOG = os.path.join(LOG_DIR, "ai_detection.jsonl")
ALERT_LOG = os.path.join(LOG_DIR, "alert_events.jsonl")
ROBOT_LOG = os.path.join(LOG_DIR, "robot_action.jsonl")

def validate_file(path: str, log_type: str) -> bool:
    if not os.path.exists(path):
        print(f"[WARN] Log file not found: {path}")
        return True # if no run occurred, log could be empty, but let's check it if it exists.
        
    print(f"Validating {log_type} log: {path} ...")
    lines_checked = 0
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                data = json.loads(line_str)
            except json.JSONDecodeError as e:
                print(f"[ERROR] Line {line_num} in {path} is not valid JSON: {e}")
                return False
                
            # Basic validation
            required_keys = ["demo_run_id", "scenario_id", "scenario_source", "zone_id", "timestamp"]
            # Robot log and Alert log require event_type
            if log_type in ["alert", "robot"]:
                required_keys.append("event_type")
                
            for k in required_keys:
                if k not in data:
                    print(f"[ERROR] Line {line_num} in {path} is missing key: '{k}'")
                    return False
                    
            if log_type == "ai":
                if "predicted_level" not in data or "rationale" not in data:
                    print(f"[ERROR] Line {line_num} in AI log is missing 'predicted_level' or 'rationale'")
                    return False
            elif log_type == "alert":
                if "alert_id" not in data:
                    print(f"[ERROR] Line {line_num} in Alert log is missing 'alert_id'")
                    return False
            elif log_type == "robot":
                if "robot_action_id" not in data or "alert_id" not in data:
                    print(f"[ERROR] Line {line_num} in Robot log is missing 'robot_action_id' or 'alert_id'")
                    return False
                    
            lines_checked += 1
            
    print(f"[PASS] {log_type} log validation passed ({lines_checked} records).")
    return True

def main():
    print("=" * 60)
    print("VALIDATING DEMO LOG FILES")
    print("=" * 60)
    
    success = True
    success &= validate_file(AI_LOG, "ai")
    success &= validate_file(ALERT_LOG, "alert")
    success &= validate_file(ROBOT_LOG, "robot")
    
    if not success:
        print("\n[FAIL] Log validation failed!")
        sys.exit(1)
        
    print("\n[SUCCESS] All log files validated successfully!")
    sys.exit(0)

if __name__ == "__main__":
    main()
