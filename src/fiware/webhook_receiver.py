"""
Webhook Receiver - Nhận notification từ Orion
- Cập nhật Room entity khi có dữ liệu mới
"""

import json
import os
import sys
from datetime import datetime, timezone
from flask import Flask, request, jsonify
import time


# Thêm đường dẫn để import
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from src.fiware import update_room_sensors,get_room_state,upsert_entity
from src.common.config import get_config
from src.common.logging_utils import append_jsonl
from src.fiware.client import update_entity_attrs
from src.orchestration import process_ai_detector_event
from src.utils import write_orion_state_log


app = Flask(__name__)

ZONE_ID = os.getenv("ZONE_ID", "DNTU_ROOM_A101")

_processed_acks = {}

def reset_processed_acks():
    global _processed_acks
    _processed_acks.clear()



# Cache để lưu dữ liệu tạm thời
_sensor_cache = {}
_cache_time = {}

def aggregate_sensor_data(device_data: dict) -> dict:
    """
    Gộp dữ liệu từ nhiều notification vào 1 dict
    """
    global _sensor_cache, _cache_time
    
    # Cập nhật cache
    for key, value in device_data.items():
        if value is not None:
            _sensor_cache[key] = value
    
    # Cập nhật thời gian
    _cache_time = time.time()
    
    # Kiểm tra xem đã có đủ 5 attributes chưa
    required_attrs = ["temperature", "humidity", "co2", "smoke_status", "energy_consumption"]
    has_all = all(attr in _sensor_cache for attr in required_attrs)
    
    if has_all:
        # Có đủ dữ liệu, trả về và reset cache
        result = _sensor_cache.copy()
        _sensor_cache = {}
        return result
    
    return {}  # Chưa đủ dữ liệu


def _extract_value(value):
    if isinstance(value, dict) and "value" in value:
        return value["value"]
    return value


# Trong webhook_receiver.py, thêm logic gộp dữ liệu

# Cache để lưu dữ liệu tạm thời
_sensor_cache = {}
_cache_time = {}

def aggregate_sensor_data(device_data: dict) -> dict:
    """
    Gộp dữ liệu từ nhiều notification vào 1 dict
    """
    global _sensor_cache, _cache_time
    
    # Cập nhật cache
    for key, value in device_data.items():
        if value is not None:
            _sensor_cache[key] = value
    
    # Cập nhật thời gian
    _cache_time = time.time()
    
    # Kiểm tra xem đã có đủ 5 attributes chưa
    required_attrs = ["temperature", "humidity", "co2", "smoke_status", "energy_consumption"]
    has_all = all(attr in _sensor_cache for attr in required_attrs)
    
    if has_all:
        # Có đủ dữ liệu, trả về và reset cache
        result = _sensor_cache.copy()
        _sensor_cache = {}
        return result
    
    return {}  # Chưa đủ dữ liệu


@app.route('/webhook/notify', methods=['POST'])
def webhook_notify():
    """Nhận notification từ Orion"""
    global _sensor_cache
    
    data = request.get_json(silent=True) or {}
    entity = data.get("data", [{}])[0] if data.get("data") else {}
    
    # Lấy dữ liệu từ notification
    device_data = {}
    for attr in ["temperature", "humidity", "co2", "smoke_status", "energy_consumption"]:
        if attr in entity:
            device_data[attr] = entity[attr].get("value") if isinstance(entity[attr], dict) else entity[attr]
    
    print(f"Received: {device_data}")
    
    # Gộp dữ liệu
    aggregated = aggregate_sensor_data(device_data)
    
    if aggregated:
        # Đã có đủ dữ liệu, tiến hành AI detection
        print(f"Aggregated: {aggregated}")
        
        # Cập nhật Room entity
        update_room_sensors(aggregated)
       
       # Ghi log trạng thái hiện tại của Room vào file
        write_orion_state_log(ZONE_ID)
        
        # Chạy AI detection
        room_state = get_room_state(ZONE_ID)
        if room_state:
            scenario_id = room_state.get("scenario_id", {}).get("value", "SCN_CRITICAL_001")
            process_ai_detector_event(room_state, scenario_id)
    
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