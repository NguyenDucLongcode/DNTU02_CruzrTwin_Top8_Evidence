"""
Webhook Receiver - Nhận notification từ Orion
- Cập nhật Room entity khi có dữ liệu mới
- Gọi robot CRUZR khi phát hiện cháy
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
from src.robot.cruzr_client import CruzrRobotClient
from src.fiware import get_room_state, get_all_devices, get_alert_events, get_robot_actions

app = Flask(__name__)

# Khởi tạo robot client (sẽ kết nối khi cần)
robot = None


def get_robot():
    """Lazy initialization của robot client, giữ kết nối lâu dài"""
    global robot
    if robot is None:
        robot = CruzrRobotClient()
    return robot


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _extract_value(value):
    if isinstance(value, dict) and "value" in value:
        return value["value"]
    return value

def write_orion_state_log():
    """
    Ghi log Orion state: Room, Devices, AlertEvent (AI), RobotAction
    Theo file Word 4.2
    """
    log_file = "logs/orion_state.jsonl"
    os.makedirs("logs", exist_ok=True)
    
    # Lấy Room entity
    room = get_room_state() or {}
    room_id = room.get("id", f"Room:{os.getenv('ZONE_ID', 'DNTU_ROOM_A101')}")
    
    # Lấy tất cả Device entities
    all_devices = get_all_devices() or []
    device_ids = [d.get("id") for d in all_devices if d.get("id")]
    
    # Lấy AlertEvent entities (AI tạo ra)
    alert_events = get_alert_events() or []
    alert_ids = [a.get("id") for a in alert_events if a.get("id")]
    
    # Lấy RobotAction entities (robot tạo ra)
    robot_actions = get_robot_actions() or []
    robot_ids = [r.get("id") for r in robot_actions if r.get("id")]
    
    # Log đầy đủ
    log_entry = {
        "timestamp": _utc_now(),
        "demo_run_id": os.getenv("DEMO_RUN_ID", "DNTU02_TOP8_RUN_2026_001"),
        "room": room_id,
        "devices": device_ids,
        "alert_events": alert_ids,
        "robot_actions": robot_ids
    }
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    print(f"   📝 Orion state logged: {log_file}")


def send_robot_emergency(temperature: float, smoke: int):
    """Gửi lệnh khẩn cấp đến robot (giữ kết nối)"""
    robot_client = get_robot()
    
    # Kết nối nếu chưa kết nối
    if not robot_client.is_connected():
        if not robot_client.connect():
            print(f"   ❌ Cannot connect to robot at {robot_client.ip}:{robot_client.port}")
            return False
    
    try:
        # Phát cảnh báo cháy
        message = f"⚠️ CẢNH BÁO CHÁY! Nhiệt độ {temperature} độ C! Vui lòng sơ tán khẩn cấp! ⚠️"
        result = robot_client.speak(message)
        print(f"   🔊 Speak result: {result}")
        
        # Hiển thị emotion khẩn cấp
        result = robot_client.play_emotion("emergency")
        print(f"   😫 Emotion result: {result}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Robot command failed: {e}")
        return False


@app.route('/webhook/notify', methods=['POST'])
def webhook_notify():
    """Nhận notification từ Orion, cập nhật Room và gọi robot nếu cháy"""

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

    # Lấy các giá trị cảm biến
    sensor_data = {}
    for key in tracked_attrs:
        if key in entity:
            sensor_data[key] = _extract_value(entity[key])
        else:
            sensor_data[key] = 0

    # Cập nhật Room entity
    if any(sensor_data.values()):
        update_room_sensors(sensor_data)

     # Ghi log Orion state sau khi cập nhật (theo file Word 4.2)
    write_orion_state_log()
    
    # ==================================================
    # PHÁT HIỆN CHÁY -> GỌI ROBOT
    # ==================================================
    temperature = sensor_data.get("temperature", 0)
    smoke = sensor_data.get("smoke_status", 0)
    
    # Điều kiện cháy: nhiệt độ >= 50°C HOẶC (nhiệt độ >= 38°C và có khói)
    is_fire = (temperature >= 50) or (temperature >= 38 and smoke == 1)
    
    if is_fire:
        print("\n" + "🔥" * 30)
        print("🔥🔥🔥 CRITICAL ALERT! FIRE DETECTED! 🔥🔥🔥")
        print(f"   Temperature: {temperature}°C")
        print(f"   Smoke: {smoke}")
        print("🔥" * 30)
        
        # Ghi log robot action
        log_entry = {
            "timestamp": _utc_now(),
            "demo_run_id": os.getenv("DEMO_RUN_ID", "DNTU02_TOP8_RUN_2026_001"),
            "zone_id": os.getenv("ZONE_ID", "DNTU_ROOM_A101"),
            "robot_id": "CRUZR_01",
            "action_type": "VOICE_DISPLAY_GUIDANCE",
            "temperature": temperature,
            "smoke": smoke,
            "message": f"⚠️ CẢNH BÁO CHÁY! Nhiệt độ {temperature}°C!",
            "status": "DISPATCHED"
        }
        
        os.makedirs("logs", exist_ok=True)
        with open("logs/robot_actions.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        
        # GỌI ROBOT CRUZR
        print("\n🤖 Sending emergency command to robot...")
        success = send_robot_emergency(temperature, smoke)
        
        if success:
            print("   ✅ Robot emergency dispatched!")
        else:
            print("   ❌ Failed to dispatch robot")

    return jsonify({"status": "ok"}), 200


@app.route('/webhook/health', methods=['GET'])
def health_check():
    return {"status": "healthy"}, 200


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🔔 Webhook Receiver Ready")
    print("=" * 50)
    print("   URL: http://0.0.0.0:5000/webhook/notify")
    print("   Trigger: temperature >= 50°C OR (temperature >= 38°C AND smoke = 1)")
    print("=" * 50 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)