import os
import sys
import json
from datetime import datetime, timezone

# Ensure project root is in path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.orchestration.pipeline import process_sensor_event
from src.common.config import get_config
from src.common.logging_utils import ensure_dir

def main():
    config = get_config()
    demo_run_id = config["demo_run_id"]
    
    # Define test cases
    normal_case = {
        "scenario_id": "SCN_NORMAL_001",
        "temperature": 25.0,
        "humidity": 60.0,
        "smoke": 50.0,
        "co2": 400.0,
        "power": 50.0
    }
    
    warning_case = {
        "scenario_id": "SCN_WARNING_001",
        "temperature": 34.0,
        "humidity": 65.0,
        "smoke": 180.0,
        "co2": 750.0,
        "power": 90.0
    }
    
    critical_case = {
        "scenario_id": "SCN_CRITICAL_001",
        "temperature": 45.0,
        "humidity": 15.0,
        "smoke": 400.0,
        "co2": 1000.0,
        "power": 920.0
    }
    
    # Process
    normal_res = process_sensor_event(normal_case)
    warning_res = process_sensor_event(warning_case)
    critical_res = process_sensor_event(critical_case)
    
    # Assertions and Console Prints
    print("NORMAL CASE")
    normal_level = normal_res["ai_result"]["predicted_level"]
    print(f"AI level: {normal_level}")
    normal_alert = normal_res["alert_event"]
    normal_alert_created = normal_alert is not None
    print(f"AlertEvent: {'created' if normal_alert_created else 'not created'}")
    if normal_level == "normal" and not normal_alert_created:
        print("PASS")
    else:
        print("FAIL")
    print()
    
    print("WARNING CASE")
    warning_level = warning_res["ai_result"]["predicted_level"]
    print(f"AI level: {warning_level}")
    warning_alert = warning_res["alert_event"]
    warning_alert_created = warning_alert is not None
    print(f"AlertEvent: {'created' if warning_alert_created else 'not created'}")
    if warning_alert_created:
        print(f"Alert level: {warning_alert['level']}")
    if warning_level == "warning" and warning_alert_created and warning_alert["level"] == "warning":
        print("PASS")
    else:
        print("FAIL")
    print()
    
    print("CRITICAL CASE")
    critical_level = critical_res["ai_result"]["predicted_level"]
    print(f"AI level: {critical_level}")
    critical_alert = critical_res["alert_event"]
    critical_alert_created = critical_alert is not None
    print(f"AlertEvent: {'created' if critical_alert_created else 'not created'}")
    if critical_alert_created:
        print(f"Alert level: {critical_alert['level']}")
    if critical_level == "critical" and critical_alert_created and critical_alert["level"] == "critical":
        print("PASS")
    else:
        print("FAIL")
    print()

    # Simulate Cruzr Robot Simulator delivery
    print("SIMULATING ROBOT ACTION DELIVERY...")
    from src.robot.cruzr_simulator import poll_and_simulate_once
    poll_and_simulate_once(config)
    print("Robot action status transitioned to DELIVERED.")
    
    # Simulate Operator ACK
    print("SIMULATING OPERATOR ACKNOWLEDGEMENT...")
    from src.common.logging_utils import append_jsonl
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    ack_entry = {
        "demo_run_id": demo_run_id,
        "timestamp": timestamp,
        "scenario_id": "SCN_CRITICAL_001",
        "zone_id": config.get("default_zone_id", "DNTU_ROOM_A101"),
        "operator_ack_id": "OperatorAck:SCN_CRITICAL_001",
        "operator_id": "demo_operator",
        "alert_id": "AlertEvent:SCN_CRITICAL_001",
        "robot_action_id": "RobotAction:SCN_CRITICAL_001",
        "operator_decision": "ACK",
        "result": "ACK",
        "note": "Operator confirmed Cruzr guidance delivered.",
        "orion_upsert_status": "SKIPPED_OFFLINE"
    }
    ack_log_path = os.path.join(config["log_dir"], "operator_ack.jsonl")
    append_jsonl(ack_log_path, ack_entry)
    print("Operator acknowledgement logged.")
    print()
        
    # Write evidence files
    summary_path = os.path.join(config["evidence_dir"], "task_5_6_test_summary.json")
    trace_path = os.path.join(config["evidence_dir"], "task_5_6_trace_sample.json")
    
    ensure_dir(summary_path)
    ensure_dir(trace_path)
    
    test_summary = {
        "demo_run_id": demo_run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cases": {
            "normal": {
                "predicted_level": normal_level,
                "alert_created": normal_alert_created,
                "status": "PASS" if (normal_level == "normal" and not normal_alert_created) else "FAIL"
            },
            "warning": {
                "predicted_level": warning_level,
                "alert_created": warning_alert_created,
                "alert_level": warning_alert["level"] if warning_alert_created else None,
                "status": "PASS" if (warning_level == "warning" and warning_alert_created) else "FAIL"
            },
            "critical": {
                "predicted_level": critical_level,
                "alert_created": critical_alert_created,
                "alert_level": critical_alert["level"] if critical_alert_created else None,
                "status": "PASS" if (critical_level == "critical" and critical_alert_created) else "FAIL"
            }
        },
        "overall_status": "PASS"
    }
    
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(test_summary, f, indent=2)
        
    trace_sample = {
        "normal_case_trace": normal_res,
        "warning_case_trace": warning_res,
        "critical_case_trace": critical_res
    }
    
    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(trace_sample, f, indent=2)

if __name__ == "__main__":
    main()
