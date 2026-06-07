import os
import sys
import json
import argparse

# Add project root to path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from src.common.config import LOG_DIR

def load_jsonl(path: str) -> list:
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if line_str:
                try:
                    rows.append(json.loads(line_str))
                except Exception:
                    continue
    return rows

def filter_records(records: list, demo_run_id: str, scenario_id: str) -> list:
    return [r for r in records if r.get("demo_run_id") == demo_run_id and r.get("scenario_id") == scenario_id]

def show_trace():
    parser = argparse.ArgumentParser(description="Show scenario closed loop execution trace.")
    parser.add_argument("--demo-run-id", default="DNTU02_TOP8_RUN_2026_001")
    parser.add_argument("--scenario-id", default="SCN_CRITICAL_001")
    args = parser.parse_args()
    
    demo_run_id = args.demo_run_id
    scenario_id = args.scenario_id
    
    print("=" * 80)
    print(f"CLOSED-LOOP TRACE FOR RUN: {demo_run_id} | SCENARIO: {scenario_id}")
    print("=" * 80)
    
    # 1. Telemetry logs
    sync_logs = load_jsonl(os.path.join(LOG_DIR, "orion_sync.jsonl"))
    sync_matches = filter_records(sync_logs, demo_run_id, scenario_id)
    print("\n--- 1. TELEMETRY / ORION SYNC SENSOR READINGS ---")
    if sync_matches:
        for r in sync_matches:
            print(f"[{r.get('timestamp')}] Zone: {r.get('zone_id')} | Source: {r.get('device_status')}")
            print(f"  Temp: {r.get('temperature')}°C | Humidity: {r.get('humidity')}% | CO2: {r.get('air_quality_or_co2')}ppm | Smoke: {r.get('smoke_status')} | Energy: {r.get('energy_consumption')}W")
    else:
        print("No matching sensor telemetry records found.")
        
    # 2. AI Anomaly Detection
    ai_logs = load_jsonl(os.path.join(LOG_DIR, "ai_detection.jsonl"))
    ai_matches = filter_records(ai_logs, demo_run_id, scenario_id)
    print("\n--- 2. AI ANOMALY DETECTION ENGINE ---")
    if ai_matches:
        for r in ai_matches:
            print(f"[{r.get('timestamp')}] Predicted Level: {r.get('predicted_level').upper()} | Model: {r.get('model')}")
            print(f"  Score: {r.get('anomaly_score')} | Risk: {r.get('risk_score')} | Confidence: {r.get('rule_confidence')}")
            print(f"  Rationale: {r.get('rationale')}")
            print(f"  Action: {r.get('recommended_action')}")
    else:
        print("No matching AI detection records found.")
        
    # 3. Alert Event Service
    alert_logs = load_jsonl(os.path.join(LOG_DIR, "alert_events.jsonl"))
    alert_matches = filter_records(alert_logs, demo_run_id, scenario_id)
    print("\n--- 3. ALERTEVENT SERVICE LIFECYCLE ---")
    if alert_matches:
        for r in alert_matches:
            print(f"[{r.get('timestamp')}] Event: {r.get('event_type')} | ID: {r.get('alert_id')}")
            print(f"  Level: {r.get('level').upper()} | Status: {r.get('status')} | Orion: {r.get('orion_upsert_status')}")
            if r.get("error"):
                print(f"  Error: {r.get('error')}")
    else:
        print("No matching AlertEvent records found.")
        
    # 4. Robot Action Service
    robot_logs = load_jsonl(os.path.join(LOG_DIR, "robot_action.jsonl"))
    robot_matches = filter_records(robot_logs, demo_run_id, scenario_id)
    print("\n--- 4. ROBOTACTION LIFECYCLE ---")
    if robot_matches:
        for r in robot_matches:
            print(f"[{r.get('timestamp')}] Event: {r.get('event_type')} | ID: {r.get('robot_action_id')}")
            print(f"  Robot: {r.get('robot_id')} | Status: {r.get('status')} | Adapter: {r.get('adapter')}")
            print(f"  Voice message EN: \"{r.get('message_en')}\"")
            msg_vi = r.get('message_vi', '')
            try:
                print(f"  Voice message VI: \"{msg_vi}\"")
            except UnicodeEncodeError:
                safe_msg_vi = msg_vi.encode('ascii', errors='replace').decode('ascii')
                print(f"  Voice message VI (ASCII fallback): \"{safe_msg_vi}\"")
            print(f"  Orion: {r.get('orion_upsert_status')}")
            if r.get("error"):
                print(f"  Error: {r.get('error')}")
    else:
        print("No matching RobotAction records found.")
        
    print("\n" + "=" * 80)

if __name__ == "__main__":
    show_trace()
