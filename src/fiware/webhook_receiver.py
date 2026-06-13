"""
Webhook Receiver - Nhận notification từ Orion
- Cập nhật Room entity khi có dữ liệu mới
"""

import json
import os
import sys
from datetime import datetime, timezone
from flask import Flask, request, jsonify

# Thêm đường dẫn để import
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from src.fiware.entities import update_room_sensors
from src.orchestration.task_5_6_pipeline import process_sensor_event
from src.common.config import get_config
from src.common.logging_utils import append_jsonl
from src.fiware.client import update_entity_attrs
from src.fiware.entities.entities_manager import upsert_entity

app = Flask(__name__)

_processed_acks = {}

def reset_processed_acks():
    global _processed_acks
    _processed_acks.clear()



def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _extract_value(value):
    if isinstance(value, dict) and "value" in value:
        return value["value"]
    return value


@app.route('/webhook/notify', methods=['POST'])
def webhook_notify():
    """Nhận notification từ Orion, cập nhật Room và chạy AI pipeline"""

    data = request.get_json(silent=True) or {}

    tracked_attrs = [
        "temperature",
        "humidity",
        "co2",
        "smoke_status",
        "energy_consumption",
    ]

    entity = {}
    if isinstance(data, dict) and isinstance(data.get("data"), list) and data["data"]:
        entity = data["data"][0] or {}

    # Lấy các giá trị cảm biến đã thay đổi
    changed_sensor_data = {}
    for key in tracked_attrs:
        if key in entity:
            changed_sensor_data[key] = _extract_value(entity[key])

    # Cập nhật Room entity
    if changed_sensor_data:
        update_room_sensors(changed_sensor_data)
        
        # Chạy AI pipeline và sinh Alert/RobotAction
        try:
            # Truyền thêm metadata nếu có từ entity hoặc data
            if "scenario_id" in entity:
                changed_sensor_data["scenario_id"] = _extract_value(entity["scenario_id"])
            if "demo_run_id" in entity:
                changed_sensor_data["demo_run_id"] = _extract_value(entity["demo_run_id"])
            if "zone_id" in entity:
                changed_sensor_data["zone_id"] = _extract_value(entity["zone_id"])
            if "expected_label" in entity:
                changed_sensor_data["expected_label"] = _extract_value(entity["expected_label"])
            elif "expected" in entity:
                changed_sensor_data["expected_label"] = _extract_value(entity["expected"])
                
            process_sensor_event(changed_sensor_data)
        except Exception as e:
            print(f"Error processing sensor event in webhook: {e}")

    return jsonify({"status": "ok"}), 200


@app.route('/api/operator/ack', methods=['POST'])
def operator_ack():
    """Nhận xác nhận từ Operator, cập nhật Orion và ghi nhận audit log"""
    req_data = request.get_json(silent=True) or {}
    
    cfg = get_config()
    decision = req_data.get("decision")
    if decision not in ["ACK", "ERROR"]:
        return jsonify({"error": "Invalid decision. Must be ACK or ERROR"}), 400
        
    alert_id = req_data.get("alert_id") or "AlertEvent:SCN_CRITICAL_001"
    robot_action_id = req_data.get("robot_action_id") or "RobotAction:SCN_CRITICAL_001"
    operator_id = req_data.get("operator_id") or "demo_operator"
    demo_run_id = req_data.get("demo_run_id") or cfg["demo_run_id"]
    scenario_id = req_data.get("scenario_id") or "SCN_CRITICAL_001"
    zone_id = req_data.get("zone_id") or cfg["default_zone_id"]
    note = req_data.get("note") or ("Operator confirmed Cruzr guidance delivered." if decision == "ACK" else "Operator reported error.")
    
    operator_ack_id = f"OperatorAck:{scenario_id}"
    
    # Kiểm tra Idempotency cache
    if operator_ack_id in _processed_acks:
        return jsonify(_processed_acks[operator_ack_id]), 200
        
    orion_upsert_status = "SKIPPED_OFFLINE"
    error_message = None
    
    if cfg["orion_enabled"]:
        try:
            if decision == "ACK":
                alert_status = "RESOLVED"
                robot_status = "COMPLETED"
                result = "ACK"
            else:
                alert_status = "NEEDS_REVIEW"
                robot_status = "ERROR"
                result = "ERROR"
                
            # Cập nhật AlertEvent
            alert_success = update_entity_attrs(alert_id, {
                "status": {"type": "Text", "value": alert_status}
            })
            
            # Cập nhật RobotAction
            robot_success = update_entity_attrs(robot_action_id, {
                "status": {"type": "Text", "value": robot_status}
            })
            
            # Upsert OperatorAck entity
            timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
            ack_attrs = {
                "demo_run_id": {"type": "Text", "value": demo_run_id},
                "scenario_id": {"type": "Text", "value": scenario_id},
                "zone_id": {"type": "Text", "value": zone_id},
                "operator_id": {"type": "Text", "value": operator_id},
                "alert_id": {"type": "Text", "value": alert_id},
                "robot_action_id": {"type": "Text", "value": robot_action_id},
                "operator_decision": {"type": "Text", "value": decision},
                "result": {"type": "Text", "value": result},
                "note": {"type": "Text", "value": note},
                "created_at": {"type": "DateTime", "value": timestamp}
            }
            ack_success = upsert_entity(operator_ack_id, "OperatorAck", ack_attrs)
            
            if alert_success and robot_success and ack_success:
                orion_upsert_status = "SUCCESS"
            else:
                orion_upsert_status = "FAILED"
                error_message = "One or more Orion updates returned False"
        except Exception as e:
            orion_upsert_status = "FAILED"
            error_message = str(e)
            
    # Ghi log operator_ack.jsonl
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    log_entry = {
        "demo_run_id": demo_run_id,
        "timestamp": timestamp,
        "scenario_id": scenario_id,
        "zone_id": zone_id,
        "operator_ack_id": operator_ack_id,
        "operator_id": operator_id,
        "alert_id": alert_id,
        "robot_action_id": robot_action_id,
        "operator_decision": decision,
        "result": "ACK" if decision == "ACK" else "ERROR",
        "note": note,
        "orion_upsert_status": orion_upsert_status
    }
    if error_message:
        log_entry["error_message"] = error_message
        
    ack_log_path = os.path.join(cfg["log_dir"], "operator_ack.jsonl")
    append_jsonl(ack_log_path, log_entry)
    
    # Trả response
    response_status = "acknowledged" if decision == "ACK" else "error_reported"
    res = {
        "status": response_status,
        "operator_decision": decision,
        "alert_id": alert_id,
        "robot_action_id": robot_action_id,
        "operator_ack_id": operator_ack_id,
        "orion_upsert_status": orion_upsert_status
    }
    if error_message:
        res["error_message"] = error_message
        
    _processed_acks[operator_ack_id] = res
    
    return jsonify(res), 200


@app.route('/webhook/health', methods=['GET'])
def health_check():
    return {"status": "healthy"}, 200



if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("Webhook Receiver Ready")
    print("=" * 50)
    print("   URL: http://0.0.0.0:5000/webhook/notify")
    print("=" * 50 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)