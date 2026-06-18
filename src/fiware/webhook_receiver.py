"""
Webhook Receiver - Nhận notification từ Orion
- Cập nhật Room entity khi có dữ liệu mới
"""

import json
import os
import sys
from datetime import datetime, timezone
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import time
import threading
# Thêm đường dẫn để import
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from src.fiware import update_room_sensors,get_room_state,upsert_entity
from src.iot.devices import BUILDING_ID, DEMO_RUN_ID
from src.common.config import get_config
from src.common.logging_utils import append_jsonl
from src.fiware.client import update_entity_attrs
from src.orchestration import process_ai_detector_event
from src.utils import write_orion_state_log
from src.utils.fire_simulator import simulate_fire_gradually, reset_simulation

app = Flask(__name__, static_folder=ROOT_DIR, static_url_path='')
CORS(app)

try:
    from src.robot.cruzr_client import CruzrRobotClient
    from src.iot.devices import DEVICES_TO_REGISTER
    if os.getenv("CRUZR_IP"):
        robot_client = CruzrRobotClient()
        threading.Thread(target=robot_client.connect, daemon=True).start()
        print("[SYSTEM] Init Cruzr Robot Client")
    else:
        robot_client = None
        print("[SYSTEM] Cruzr Robot Client skipped because CRUZR_IP is not set")
except Exception as e:
    robot_client = None
    print(f"[SYSTEM WARNING] Robot Init Error: {e}")

ZONE_ID = os.getenv("ZONE_ID", "DNTU_ROOM_A101")

ROOM_DISPLAY_TO_CODE = {
    f"L1-A{index}": f"A{100 + index}"
    for index in range(1, 13)
}

def normalize_zone_id(entity_id: str) -> str:
    token = (entity_id or "").split(":")[-1].split("_")[-1]
    token = token.removeprefix("DNTU_ROOM_")
    token = ROOM_DISPLAY_TO_CODE.get(token, token)
    return f"DNTU_ROOM_{token}" if token else ZONE_ID

def ensure_room_entity(zone_id: str, timestamp: str) -> bool:
    room_code = zone_id.replace("DNTU_ROOM_", "")
    attrs = {
        "demo_run_id": {"type": "Text", "value": DEMO_RUN_ID},
        "zone_id": {"type": "Text", "value": zone_id},
        "room_id": {"type": "Text", "value": room_code},
        "building_id": {"type": "Text", "value": BUILDING_ID},
        "floor": {"type": "Number", "value": 1},
        "room_name": {"type": "Text", "value": room_code},
        "room_type": {"type": "Text", "value": "Classroom"},
        "capacity": {"type": "Number", "value": 50},
        "scenario_id": {"type": "Text", "value": "SCN_CRITICAL_001"},
        "device_status": {"type": "Text", "value": "ON"},
        "device_ids": {"type": "Array", "value": []},
        "anomaly_detected": {"type": "Boolean", "value": False},
        "robot_response_required": {"type": "Boolean", "value": False},
        "robot_status": {"type": "Text", "value": "idle"},
        "evacuation_status": {"type": "Text", "value": "normal"},
        "emergency_level": {"type": "Text", "value": "normal"},
        "timestamp": {"type": "DateTime", "value": timestamp},
        "last_updated": {"type": "DateTime", "value": timestamp},
    }
    return upsert_entity(f"Room:{zone_id}", "Room", attrs)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_jsonl_file(relative_path: str, limit: int = 20) -> list:
    logs = []
    file_path = os.path.join(ROOT_DIR, relative_path)
    if not os.path.exists(file_path):
        return logs
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f.readlines()[-limit:]:
            try:
                logs.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue
    return logs


def mongo_timestamp_to_iso(value) -> str:
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    if isinstance(value, str):
        return value
    return utc_now()


def get_sensor_readings_from_mongo(limit: int = 20) -> list:
    try:
        import pymongo
        client = pymongo.MongoClient(
            f"mongodb://{os.getenv('MONGO_HOST', 'localhost')}:27017/",
            serverSelectionTimeoutMS=2000
        )
        db = client["orion-cruzrtwin"]
        entities = list(db["entities"].find({"_id.id": {"$regex": "^Device:"}}, {"_id": 1, "attrs": 1}).limit(limit * 2))
    except Exception:
        return read_jsonl_file("logs/sensorReading.jsonl", limit)

    readings = []
    for entity in entities:
        entity_id = entity.get("_id", {}).get("id", "")
        attrs = entity.get("attrs", {}) or {}
        zone_id = normalize_zone_id(entity_id)
        room_code = zone_id.replace("DNTU_ROOM_", "")
        timestamp_value = attrs.get("TimeInstant", {}).get("value") if isinstance(attrs.get("TimeInstant"), dict) else attrs.get("TimeInstant")

        if "TEMP" in entity_id:
            attr = attrs.get("temperature", {})
            value = attr.get("value", 0) if isinstance(attr, dict) else attr
            status = "CRITICAL" if float(value or 0) >= 37 else "WARNING" if float(value or 0) >= 32 else "NORMAL"
            readings.append({
                "timestamp": mongo_timestamp_to_iso(timestamp_value),
                "demo_run_id": DEMO_RUN_ID,
                "zone_id": zone_id,
                "room": room_code,
                "device_id": entity_id,
                "sensor_type": "TEMPERATURE",
                "temperature": value,
                "temp": value,
                "device_status": status,
            })
        elif "SMOKE" in entity_id:
            attr = attrs.get("smoke_status", {})
            value = attr.get("value", 0) if isinstance(attr, dict) else attr
            status = "CRITICAL" if float(value or 0) >= 1 else "NORMAL"
            readings.append({
                "timestamp": mongo_timestamp_to_iso(timestamp_value),
                "demo_run_id": DEMO_RUN_ID,
                "zone_id": zone_id,
                "room": room_code,
                "device_id": entity_id,
                "sensor_type": "SMOKE",
                "smoke_status": value,
                "smoke": value,
                "device_status": status,
            })
        elif "AIR" in entity_id:
            attr = attrs.get("co2", {})
            value = attr.get("value", 400) if isinstance(attr, dict) else attr
            status = "CRITICAL" if float(value or 0) >= 920 else "WARNING" if float(value or 0) >= 631 else "NORMAL"
            readings.append({
                "timestamp": mongo_timestamp_to_iso(timestamp_value),
                "demo_run_id": DEMO_RUN_ID,
                "zone_id": zone_id,
                "room": room_code,
                "device_id": entity_id,
                "sensor_type": "AIR_QUALITY",
                "co2": value,
                "air_quality_or_co2": value,
                "device_status": status,
            })
        elif "PRESENCE" in entity_id:
            attr = attrs.get("presence", {})
            value = attr.get("value", 0) if isinstance(attr, dict) else attr
            readings.append({
                "timestamp": mongo_timestamp_to_iso(timestamp_value),
                "demo_run_id": DEMO_RUN_ID,
                "zone_id": zone_id,
                "room": room_code,
                "device_id": entity_id,
                "sensor_type": "PRESENCE",
                "presence": value,
                "device_status": "OCCUPIED" if float(value or 0) > 0 else "EMPTY",
            })

    readings.sort(key=lambda item: item.get("timestamp", ""), reverse=True)
    return readings[:limit]

_processed_acks = {}
# Cache để lưu dữ liệu tạm thời theo từng phòng
_sensor_cache = {}
_cache_time = {}

def aggregate_sensor_data(room_code: str, device_data: dict) -> dict:
    """
    Gộp dữ liệu từ nhiều notification vào 1 dict theo từng phòng
    """
    global _sensor_cache, _cache_time

    if room_code not in _sensor_cache:
        _sensor_cache[room_code] = {
            "humidity": 50.0,
            "energy_consumption": 0.0
        }

    # Cập nhật cache
    for key, value in device_data.items():
        if value is not None:
            _sensor_cache[room_code][key] = value

    # Cập nhật thời gian
    _cache_time[room_code] = time.time()

    return _sensor_cache[room_code].copy()


def _extract_value(value):
    if isinstance(value, dict) and "value" in value:
        return value["value"]
    return value


@app.route('/webhook/notify', methods=['POST'])
def webhook_notify():
    """Nhận notification từ Orion"""
    global _sensor_cache

    data = request.get_json(silent=True) or {}
    entity = data.get("data", [{}])[0] if data.get("data") else {}

    entity_id = entity.get("id", "")
    zone_id = normalize_zone_id(entity_id)

    # Lấy dữ liệu từ notification
    device_data = {}
    for attr in ["temperature", "humidity", "co2", "smoke_status", "energy_consumption"]:
        if attr in entity:
            device_data[attr] = entity[attr].get("value") if isinstance(entity[attr], dict) else entity[attr]

    # Gộp dữ liệu
    aggregated = aggregate_sensor_data(zone_id.replace("DNTU_ROOM_", ""), device_data)

    if aggregated:
        timestamp = utc_now()
        ensure_room_entity(zone_id, timestamp)
        # Cập nhật Room entity
        update_room_sensors(aggregated, zone_id=zone_id)

        # Ghi log trạng thái hiện tại của Room vào file
        write_orion_state_log(zone_id)

        # Chạy AI detection
        room_state = get_room_state(zone_id)
        if room_state:
            scenario_id = room_state.get("scenario_id", {}).get("value", "SCN_CRITICAL_001")
            res = process_ai_detector_event(room_state, scenario_id)

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

@app.route('/api/operator/ack', methods=['POST'])
def operator_ack():
    """Nhận xác nhận từ Operator, cập nhật Orion và ghi nhận audit log"""

    req_data = request.get_json(silent=True) or {}
    cfg = get_config()

    decision = req_data.get("decision", "").upper()

    if decision not in ["ACK", "ERROR"]:
        return jsonify({
            "error": "Invalid decision. Must be ACK or ERROR"
        }), 400

    alert_id = req_data.get("alert_id") or "AlertEvent:SCN_CRITICAL_001"
    robot_action_id = req_data.get("robot_action_id") or "RobotAction:CRUZR_ACTION_001"
    operator_id = req_data.get("operator_id") or "demo_operator"
    demo_run_id = req_data.get("demo_run_id") or cfg["demo_run_id"]
    scenario_id = req_data.get("scenario_id") or "SCN_CRITICAL_001"
    zone_id = req_data.get("zone_id") or cfg["default_zone_id"]

    note = req_data.get("note") or (
        "Operator confirmed Cruzr guidance delivered."
        if decision == "ACK"
        else "Operator reported error."
    )

    # Dùng alert_id để tránh trùng
    operator_ack_id = f"OperatorAck:{alert_id}"

    # Idempotency cho demo
    if operator_ack_id in _processed_acks:
        return jsonify(_processed_acks[operator_ack_id]), 200

    timestamp = (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )

    orion_upsert_status = "SKIPPED_OFFLINE"
    error_message = None

    if cfg["orion_enabled"]:
        try:

            if decision == "ACK":
                alert_status = "RESOLVED"
                robot_status = "COMPLETED"
                result = "ACK"
                operator_decision = "ACKNOWLEDGED"

            else:
                alert_status = "NEEDS_REVIEW"
                robot_status = "ERROR"
                result = "ERROR"
                operator_decision = "ERROR_REPORTED"

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
        "zone_id": zone_id,
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


@app.route('/webhook/health', methods=['GET'])
def health_check():
    return {"status": "healthy"}, 200

# ==========================================
# GIAO DIỆN FRONTEND (DASHBOARD)
# ==========================================
@app.route('/')
def serve_root():
    return app.send_static_file('dashboard.html')

@app.route('/<path:path>')
def serve_static(path):
    return app.send_static_file(path)

# ==========================================
# DASHBOARD APIs
# ==========================================
@app.route('/api/robot/command', methods=['POST'])
def api_robot_command():
    cmd = request.get_json(silent=True) or {}
    action = cmd.get('action')
    print(f"[ROBOT] Command: {action}")
    
    result = {"success": False, "message": "Robot not connected"}
    if robot_client and robot_client.is_connected():
        if action == 'move_forward': result = robot_client.move_forward()
        elif action == 'move_backward': result = robot_client.move_backward()
        elif action == 'turn_left': result = robot_client.turn_left()
        elif action == 'turn_right': result = robot_client.turn_right()
        elif action == 'stop': result = robot_client.stop()
        elif action == 'emergency': result = robot_client.emergency_evacuation(cmd.get('room', 'A101'))
        elif action == 'speak': result = robot_client.speak(cmd.get('text', 'Hello'))
    return jsonify(result), 200

# ==========================================
# ADMIN CONTROL APIs
# ==========================================
@app.route('/api/admin/simulate/fire', methods=['POST'])
def api_admin_simulate_fire():
    req = request.get_json(silent=True) or {}
    room_id = req.get('room_id', 'A101')
    severity = req.get('severity', 'large')
    
    print(f"[ADMIN] Admin requested fire simulation in room {room_id}")
    simulate_fire_gradually(room_id, severity)
    return jsonify({"success": True, "message": f"Cấu hình thiết bị đã được đổi sang CHÁY ở {room_id}"}), 200

@app.route('/api/admin/simulate/reset', methods=['POST'])
def api_admin_simulate_reset():
    req = request.get_json(silent=True) or {}
    room_id = req.get('room_id', 'A101')
    
    print(f"[ADMIN] Admin requested reset simulation in room {room_id}")
    from src.utils.fire_simulator import reset_simulation
    reset_simulation(room_id)
    
    global _processed_acks
    _processed_acks.clear()
    
    return jsonify({"success": True, "message": f"Thiết bị ở {room_id} đã trở về TRỐNG (Không có người)"}), 200

@app.route('/api/admin/simulate/presence', methods=['POST'])
def api_admin_simulate_presence():
    req = request.get_json(silent=True) or {}
    room_id = req.get('room_id', 'A101')
    
    print(f"[ADMIN] Admin requested active presence simulation in room {room_id}")
    from src.utils.fire_simulator import set_active_simulation
    set_active_simulation(room_id)
    
    global _processed_acks
    _processed_acks.clear()
    
    return jsonify({"success": True, "message": f"Thiết bị ở {room_id} đã chuyển sang CÓ NGƯỜI (Hoạt động)"}), 200

@app.route('/api/logs/<log_type>', methods=['GET'])
def api_get_logs(log_type):
    log_map = {
        'ai': 'logs/ai_detection.jsonl',
        'alerts': 'logs/alert_events.jsonl',
        'state': 'logs/orion_state.jsonl',
        'robot': 'logs/robot_actions.jsonl',
        'sensors': 'logs/sensorReading.jsonl',
        'ack': 'logs/operator_ack.jsonl'
    }
    file_path = log_map.get(log_type)

    if log_type == 'sensors':
        logs = get_sensor_readings_from_mongo(limit=20)
        return jsonify(logs), 200

    logs = read_jsonl_file(file_path) if file_path else []
    return jsonify(logs), 200

@app.route('/api/robot/status', methods=['GET'])
def api_robot_status():
    status = {"connected": False, "battery": 0, "location": {"x": 0, "y": 0}}
    if robot_client:
        rs = robot_client.get_status()
        status = {
            "connected": robot_client.is_connected(),
            "battery": rs.battery_level,
            "location": {"x": rs.current_x, "y": rs.current_y},
            "charging": rs.is_charging
        }
    return jsonify(status), 200

@app.route('/api/devices', methods=['GET'])
def api_devices():
    if 'DEVICES_TO_REGISTER' in globals():
        return jsonify(DEVICES_TO_REGISTER), 200
    return jsonify([]), 200

@app.route('/api/db/sensors', methods=['GET'])
def api_db_sensors():
    try:
        import pymongo
        mongo_host = os.getenv('MONGO_HOST', 'localhost')
        client = pymongo.MongoClient(f'mongodb://{mongo_host}:27017/', serverSelectionTimeoutMS=2000)
        db = client['orion-cruzrtwin']
        entities = db['entities'].find({})
        
        room_data = {}
        for ent in entities:
            ent_id = ent.get('_id', {}).get('id', '')
            if not ent_id.startswith('Device:'): continue
            
            room = ent_id.split('_')[-1]
            if room not in room_data:
                room_data[room] = {"temp": 25.0, "smoke": 0.0, "co2": 400.0, "presence": 0}
            
            attrs = ent.get('attrs', {})
            if 'TEMP' in ent_id:
                room_data[room]["temp"] = attrs.get('temperature', {}).get('value', 25.0)
            elif 'SMOKE' in ent_id:
                room_data[room]["smoke"] = attrs.get('smoke_status', {}).get('value', 0.0)
            elif 'AIR' in ent_id:
                room_data[room]["co2"] = attrs.get('co2', {}).get('value', 400.0)
            elif 'PRESENCE' in ent_id:
                room_data[room]["presence"] = attrs.get('presence', {}).get('value', 0)
        
        return jsonify(room_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("DNTU Digital Twin Backend Ready")
    print("=" * 50)
    print("   Dashboard: http://0.0.0.0:5000/dashboard.html")
    print("=" * 50 + "\n")

    def auto_register_subscription():
        import time
        from src.fiware.subscription import ensure_subscription_for_devices, get_all_subscriptions
        print("[SYSTEM] Waiting for Orion to start to auto-register subscriptions...")
        
        for _ in range(12): # Thử tối đa 12 lần (60 giây)
            time.sleep(5)
            try:
                subs = get_all_subscriptions()
                if subs:
                    print("[SYSTEM] Subscription already exists.")
                    ensure_subscription_for_devices()
                    break
                subscription_id = ensure_subscription_for_devices()
                if subscription_id:
                    print("[SYSTEM] Subscription created.")
                    break
            except Exception as e:
                print(f"[SYSTEM] Orion not ready yet, retrying... ({e})")
                
    threading.Thread(target=auto_register_subscription, daemon=True).start()

    app.run(host='0.0.0.0', port=5000, debug=False)
