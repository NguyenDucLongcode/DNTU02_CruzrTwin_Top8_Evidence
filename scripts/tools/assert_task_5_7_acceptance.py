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

def load_jsonl(path: str) -> list:
    if not os.path.exists(path):
        return []
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    records.append(json.loads(line.strip()))
                except Exception:
                    continue
    return records

def assert_acceptance():
    print("=" * 60)
    print("TESTING SYSTEM COMPLIANCE AND ACCEPTANCE CRITERIA")
    print("=" * 60)
    
    ai_records = load_jsonl(AI_LOG)
    alert_records = load_jsonl(ALERT_LOG)
    robot_records = load_jsonl(ROBOT_LOG)
    
    from collections import defaultdict
    scenarios_ai = defaultdict(list)
    for r in ai_records:
        sc_id = r.get("scenario_id")
        if sc_id:
            scenarios_ai[sc_id].append(r)
            
    # 1. Assert Normal Scenario Compliance
    print("Verifying NORMAL scenario behavior...")
    normal_scenarios = [s for s in scenarios_ai if "normal" in s.lower()]
    for sc_id in normal_scenarios:
        last_rec = scenarios_ai[sc_id][-1]
        if last_rec.get("predicted_level") != "normal":
            print(f"[FAIL] Normal scenario {sc_id} final AI result is {last_rec.get('predicted_level')}")
            sys.exit(1)
            
    # Check that no alerts or robot actions were created for normal scenarios
    for record in alert_records:
        if "normal" in record.get("scenario_id").lower():
            print(f"[FAIL] Found AlertEvent created for a normal scenario!")
            sys.exit(1)
    for record in robot_records:
        if "normal" in record.get("scenario_id").lower():
            print(f"[FAIL] Found RobotAction created for a normal scenario!")
            sys.exit(1)
    print("[PASS] Normal Scenario checks passed.")
    
    # 2. Assert Warning Scenario Compliance
    print("Verifying WARNING scenario behavior...")
    warning_scenarios = [s for s in scenarios_ai if "warning" in s.lower()]
    for sc_id in warning_scenarios:
        last_rec = scenarios_ai[sc_id][-1]
        if last_rec.get("predicted_level") != "warning":
            print(f"[FAIL] Warning scenario {sc_id} final AI result is {last_rec.get('predicted_level')}")
            sys.exit(1)
            
    # Verify AlertEvent created for warning scenarios
    warning_alerts = [r for r in alert_records if "warning" in r.get("scenario_id").lower()]
    if not warning_alerts:
        print("[FAIL] No AlertEvent created for warning scenarios.")
        sys.exit(1)
        
    # Verify no RobotAction created for warning scenarios
    for record in robot_records:
        if "warning" in record.get("scenario_id").lower():
            print("[FAIL] Found RobotAction created for a warning scenario!")
            sys.exit(1)
    print("[PASS] Warning Scenario checks passed.")
    
    # 3. Assert Critical Scenario Compliance
    print("Verifying CRITICAL scenario behavior...")
    critical_scenarios = [s for s in scenarios_ai if "critical" in s.lower()]
    for sc_id in critical_scenarios:
        last_rec = scenarios_ai[sc_id][-1]
        if last_rec.get("predicted_level") != "critical":
            print(f"[FAIL] Critical scenario {sc_id} final AI result is {last_rec.get('predicted_level')}")
            sys.exit(1)
            
    # Verify AlertEvent created for critical scenarios
    critical_alerts = [r for r in alert_records if "critical" in r.get("scenario_id").lower()]
    if not critical_alerts:
        print("[FAIL] No AlertEvent created for critical scenarios.")
        sys.exit(1)
        
    # Verify RobotAction created for critical scenarios
    critical_robots = [r for r in robot_records if "critical" in r.get("scenario_id").lower()]
    if not critical_robots:
        print("[FAIL] No RobotAction created for critical scenarios.")
        sys.exit(1)
        
    # Verify Robot status is GUIDANCE_DELIVERED or ACK_WAITING
    final_robot_status = critical_robots[-1].get("status")
    if final_robot_status not in ["GUIDANCE_DELIVERED", "ACK_WAITING"]:
        print(f"[FAIL] RobotAction status is {final_robot_status}, expected GUIDANCE_DELIVERED or ACK_WAITING.")
        sys.exit(1)
        
    print("[PASS] Critical Scenario checks passed.")
    print("\nALL TASKS 5-7 ACCEPTANCE CRITERIA ARE FULLY PASSED!")
    print("=" * 60)
    sys.exit(0)

if __name__ == "__main__":
    assert_acceptance()
