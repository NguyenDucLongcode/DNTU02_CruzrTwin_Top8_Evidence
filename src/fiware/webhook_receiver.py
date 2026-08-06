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

    # Gộp dữ liệu
    aggregated = aggregate_sensor_data(device_data)

    if aggregated:

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


# ==========================================
# API: Operator ACK / ERROR
# http://127.0.0.1:5000/api/operator/ack
# Payload body ví dụ:
#
# {
#   "decision": "ACK",
#   "alert_id": "AlertEvent:SCN_CRITICAL_001",
#   "robot_action_id": "RobotAction:CRUZR_ACTION_001",
#   "operator_id": "demo_operator",
#   "demo_run_id": "DNTU02_TOP8_RUN_2026_001",
#   "scenario_id": "SCN_CRITICAL_001",
#   "zone_id": "DNTU_ROOM_A101",
#   "note": "Operator confirmed Cruzr guidance delivered."
# }
#
# decision chỉ nhận:
# - ACK
# - ERROR
# ==========================================

_processed_acks = {}

@app.route('/api/operator/ack', methods=['POST'])
def operator_ack():
    """Nhận xác nhận từ Operator, cập nhật Orion và ghi nhận audit log"""

    req_data = request.get_json(silent=True) or {}
    cfg = get_config()

    decision = req_data.get("decision", "").upper()

    valid_decisions = ["ACK", "ERROR", "ROBOT_RETRY", "RETRY", "UNDO", "NORMAL", "WARNING", "CRITICAL"]
    if decision not in valid_decisions:
        return jsonify({
            "error": f"Invalid decision. Must be one of {valid_decisions}"
        }), 400

    alert_id = req_data.get("alert_id") or "AlertEvent:SCN_CRITICAL_001"
    robot_action_id = req_data.get("robot_action_id") or "RobotAction:CRUZR_ACTION_001"
    operator_id = req_data.get("operator_id") or "demo_operator"
    demo_run_id = req_data.get("demo_run_id") or cfg["demo_run_id"]
    scenario_id = req_data.get("scenario_id") or "SCN_CRITICAL_001"
    zone_id = req_data.get("zone_id") or cfg["default_zone_id"]

    note = req_data.get("note") or f"Operator decision: {decision}"

    # Dùng alert_id để định danh
    operator_ack_id = f"OperatorAck:{alert_id}"

    timestamp = (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )

    orion_upsert_status = "SKIPPED_OFFLINE"
    error_message = None

    if cfg["orion_enabled"]:
        try:

            if decision in ["ACK", "NORMAL"]:
                alert_status = "RESOLVED"
                robot_status = "COMPLETED"
                result = decision
                operator_decision = "ACKNOWLEDGED"
            elif decision in ["ERROR", "CRITICAL"]:
                alert_status = "NEEDS_REVIEW"
                robot_status = "ERROR"
                result = decision
                operator_decision = "ERROR_REPORTED"
            elif decision in ["ROBOT_RETRY", "RETRY"]:
                try:
                    from src.robot.create_robot_action import test_robot_connection
                    retry_res = test_robot_connection()
                    note = retry_res.get("message", "Robot retry executed")
                except Exception as e:
                    note = f"Robot retry check: {e}"
                alert_status = "RETRYING"
                robot_status = "PENDING"
                result = "RETRY"
                operator_decision = "RETRY_TRIGGERED"
            elif decision == "UNDO":
                alert_status = "PENDING"
                robot_status = "PENDING"
                result = "UNDO"
                operator_decision = "ACTION_UNDONE"
            else:
                alert_status = "REVIEWING"
                robot_status = "PENDING"
                result = decision
                operator_decision = f"{decision}_REPORTED"

            # Update AlertEvent
            alert_success = update_entity_attrs(
                alert_id,
                {
                    "status": {
                        "type": "Text",
                        "value": alert_status
                    }
                }
            )

            # Update RobotAction
            robot_success = update_entity_attrs(
                robot_action_id,
                {
                    "status": {
                        "type": "Text",
                        "value": robot_status
                    }
                }
            )

            # Upsert OperatorAck entity
            ack_attrs = {
                "demo_run_id": {
                    "type": "Text",
                    "value": demo_run_id
                },
                "scenario_id": {
                    "type": "Text",
                    "value": scenario_id
                },
                "zone_id": {
                    "type": "Text",
                    "value": zone_id
                },
                "operator_id": {
                    "type": "Text",
                    "value": operator_id
                },
                "alert_id": {
                    "type": "Text",
                    "value": alert_id
                },
                "robot_action_id": {
                    "type": "Text",
                    "value": robot_action_id
                },
                "operator_decision": {
                    "type": "Text",
                    "value": operator_decision
                },
                "result": {
                    "type": "Text",
                    "value": result
                },
                "note": {
                    "type": "Text",
                    "value": note
                },
                "created_at": {
                    "type": "DateTime",
                    "value": timestamp
                }
            }

            ack_success = upsert_entity(
                operator_ack_id,
                "OperatorAck",
                ack_attrs
            )

            if alert_success and robot_success and ack_success:
                orion_upsert_status = "SUCCESS"
            else:
                orion_upsert_status = "FAILED"
                error_message = (
                    "One or more Orion updates returned False"
                )

        except Exception as e:
            orion_upsert_status = "FAILED"
            error_message = str(e)

    else:
        operator_decision = (
            "ACKNOWLEDGED"
            if decision == "ACK"
            else "ERROR_REPORTED"
        )

        result = decision
# ==========================================
    # Log theo đúng yêu cầu 4.5
    # ==========================================

    log_entry = {
        "demo_run_id": demo_run_id,
        "timestamp": timestamp,
        "operator_id": operator_id,
        "alert_id": alert_id,
        "robot_action_id": robot_action_id,
        "operator_decision": operator_decision,
        "result": result,
        "note": note
    }

    ack_log_path = os.path.join(
        cfg["log_dir"],
        "operator_ack.jsonl"
    )

    append_jsonl(ack_log_path, log_entry)

    response_status = (
        "acknowledged"
        if decision == "ACK"
        else "error_reported"
    )

    res = {
        "status": response_status,
        "operator_ack_id": operator_ack_id,
        "alert_id": alert_id,
        "robot_action_id": robot_action_id,
        "orion_upsert_status": orion_upsert_status
    }

    if error_message:
        res["error_message"] = error_message

    _processed_acks[operator_ack_id] = res

    return jsonify(res), 200


def _read_jsonl(filepath: str) -> list:
    """Read a JSONL file and return a list of dicts in chronological order (oldest first)."""
    if not os.path.exists(filepath):
        return []
    records = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


LOG_ROUTES = {
    "sensors": "sensorReading.jsonl",
    "state": "orion_state.jsonl",
    "ai": "ai_detection.jsonl",
    "robot": "robot_actions.jsonl",
    "ack": "operator_ack.jsonl",
}


@app.route('/api/logs/<log_type>', methods=['GET'])
def api_logs(log_type):
    """Return log entries for the given log type."""
    filename = LOG_ROUTES.get(log_type)
    if not filename:
        return jsonify({"error": f"Unknown log type: {log_type}"}), 404
    cfg = get_config()
    filepath = os.path.join(cfg["log_dir"], filename)
    return jsonify(_read_jsonl(filepath)), 200


@app.route('/api/db/sensors', methods=['GET'])
def api_db_sensors():
    """Return the latest sensor reading per zone_id grouped as {room_id: {temp, smoke, co2, device_status}}.
    Keys are in L1-A{n} format (e.g. L1-A1, L1-A12) for frontend 3D/map lookup.
    """
    import re
    cfg = get_config()
    filepath = os.path.join(cfg["log_dir"], "sensorReading.jsonl")
    records = _read_jsonl(filepath)
    latest_per_zone = {}
    for rec in records:
        zone = rec.get("zone_id") or rec.get("room")
        if not zone:
            continue
        match = re.search(r'A(\d+)', zone)
        if match:
            room_num = int(match.group(1)) - 100
            room_key = f"L1-A{room_num}"
        else:
            room_key = zone.replace("DNTU_ROOM_", "")
        latest_per_zone[room_key] = {
            "temp": rec.get("temperature"),
            "smoke": rec.get("smoke_status"),
            "co2": rec.get("air_quality_or_co2"),
            "device_status": rec.get("device_status"),
        }
    return jsonify(latest_per_zone), 200


def remove_last_log_line():
    """Xóa dòng log vừa thực hiện gần nhất khỏi các file logs (Undo khi bấm Reset Demo 1 lần)"""
    log_files = [
        "sensorReading.jsonl",
        "sensor_readings.jsonl",
        "orion_state.jsonl",
        "ai_detection.jsonl",
        "alert_events.jsonl",
        "robot_actions.jsonl",
        "operator_ack.jsonl",
        "operator_acks.jsonl"
    ]
    logs_dir = os.path.join(ROOT_DIR, "logs")
    for filename in log_files:
        filepath = os.path.join(logs_dir, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                if lines:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.writelines(lines[:-1])
            except Exception as e:
                print(f"Error removing last line from {filename}: {e}")


@app.route('/api/scenario/run', methods=['POST'])
def run_scenario():
    """Kích hoạt chạy kịch bản mô phỏng (normal, warning, critical, undo, reset_all)"""
    req_data = request.get_json(silent=True) or {}
    scenario_type = req_data.get("scenario", "normal").lower()

    # Xóa cache bộ nhớ trong Flask server
    try:
        from src.alerts.alert_service import reset_alert_service_cache
        from src.robot.create_robot_action import reset_robot_action_cache
        reset_alert_service_cache()
        reset_robot_action_cache()
        reset_processed_acks()
    except Exception as e:
        print(f"Warning clearing in-memory caches: {e}")

    # Hàm hỗ trợ bật lại điện Smart Plug và tắt Còi báo động khi về Normal / Reset
    def restore_tuya_devices():
        try:
            from src.tuya import control_multiple_by_fiware_ids
            all_plugs = [
                "smart_plug_a101",
                "smart_plug_a102",
                "smart_plug_a103",
                "smart_plug_a104",
                "smart_plug_a105",
                "smart_plug_a106",
            ]
            all_alarms = [
                "audible_alarm_a101"
            ]
            print(f"🔌 [RESTORE IOT] Đang cấp điện lại cho toàn bộ {len(all_plugs)} ổ cắm Smart Plug...")
            control_multiple_by_fiware_ids(all_plugs, action="on", device_type="smart_plug", max_workers=len(all_plugs))
            print(f"🔕 [RESTORE IOT] Đang tắt toàn bộ {len(all_alarms)} còi báo động Alarm...")
            control_multiple_by_fiware_ids(all_alarms, action="off", device_type="alarm", max_workers=len(all_alarms))
        except Exception as err:
            print(f"Restore Tuya devices note: {err}")

    # Nút Reset Demo: Ấn 1 lần (undo) -> xóa log vừa thực hiện gần nhất
    if scenario_type in ["undo", "undo_last"]:
        remove_last_log_line()
        threading.Thread(target=restore_tuya_devices, daemon=True).start()
        return jsonify({
            "success": True,
            "message": "Action undone: Removed last log entry & restored IoT devices"
        }), 200

    # Nút Reset Demo: Ấn 3 lần (reset_all/reset) -> xóa toàn bộ log
    if scenario_type in ["reset", "reset_all"]:
        log_files = [
            "sensorReading.jsonl",
            "sensor_readings.jsonl",
            "orion_state.jsonl",
            "ai_detection.jsonl",
            "alert_events.jsonl",
            "robot_actions.jsonl",
            "operator_ack.jsonl",
            "operator_acks.jsonl"
        ]
        logs_dir = os.path.join(ROOT_DIR, "logs")
        for filename in log_files:
            filepath = os.path.join(logs_dir, filename)
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception as e:
                    print(f"Error deleting log file {filename}: {e}")
        threading.Thread(target=restore_tuya_devices, daemon=True).start()
        return jsonify({
            "success": True,
            "message": "Reset all demo logs completely!"
        }), 200

    # Nút Robot Retry: Kiểm tra kết nối Robot và trả thông báo lên UI (Không ghi log ACK)
    if scenario_type in ["robot_retry", "retry"]:
        try:
            from src.robot.create_robot_action import test_robot_connection
            retry_res = test_robot_connection()
            return jsonify({
                "success": True,
                "message": retry_res.get("message", "Robot Retry connection check completed"),
                "connected": retry_res.get("connected", False)
            }), 200
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Robot retry check notice: {e}"
            }), 500

    file_map = {
        "normal": "normal_001.json",
        "warning": "warning_001.json",
        "critical": "critical_001.json"
    }

    target_file = file_map.get(scenario_type)
    if not target_file:
        return jsonify({"success": False, "error": f"Invalid scenario type: {scenario_type}"}), 400

    file_path = os.path.join(ROOT_DIR, "data", "replay_test_set", target_file)
    if not os.path.exists(file_path):
        return jsonify({"success": False, "error": f"Dataset file not found: {file_path}"}), 404

    try:
        from pathlib import Path
        from src.utils.replay_helpers import load_test_file, extract_all_readings, extract_device_values_from_reading, build_scenario_id
        from src.orchestration.pipeline import process_sensor_event

        test_data = load_test_file(Path(file_path))
        readings = extract_all_readings(test_data)
        scenario_id = build_scenario_id(target_file)

        generated_count = 0
        for reading in readings:
            device_values = extract_device_values_from_reading(reading)
            payload = {
                "scenario_id": scenario_id,
                "temperature": device_values.get("temp_sensor_a101", 25.0),
                "humidity": device_values.get("humid_sensor_a101", 60.0),
                "smoke": device_values.get("smoke_sensor_a101", 0.0),
                "co2": device_values.get("air_sensor_a101", 400.0),
                "power": device_values.get("energy_sensor_e101", 50.0)
            }
            process_sensor_event(payload)
            generated_count += 1

        if scenario_type == "normal":
            threading.Thread(target=restore_tuya_devices, daemon=True).start()

        return jsonify({
            "success": True,
            "message": f"Kịch bản {scenario_type} đã thực thi thành công! Đã tạo {generated_count} bản ghi log.",
            "generated_logs": generated_count,
            "scenario": scenario_type
        }), 200
    except Exception as err:
        print(f"Error executing scenario {scenario_type}: {err}")
        return jsonify({"success": False, "error": f"Execution error: {err}"}), 500


@app.route('/webhook/health', methods=['GET'])
def health_check():
    return {"status": "healthy"}, 200



if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    print("\n" + "=" * 50)
    print("Webhook Receiver Ready")
    print("=" * 50)
    print(f"   URL: http://0.0.0.0:{port}/webhook/notify")
    print("=" * 50 + "\n")

    app.run(host='0.0.0.0', port=port, debug=False)
