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
import time 


# Thêm đường dẫn để import
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from src.fiware.entities import update_room_sensors
from src.robot.cruzr_client import CruzrRobotClient
from src.fiware import get_room_state, get_all_devices, get_alert_events, get_robot_actions
from src.tuya.commands import control_fire_emergency_plugs

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

def write_robot_action_log(alert_id: str, zone_id: str, message: str, status: str = "ACK"):
    """
    Ghi log RobotAction theo đúng format file Word 4.4
    
    Format yêu cầu:
    {
        "demo_run_id": "DNTU02_TOP8_RUN_2026_001",
        "timestamp": "2026-05-17T09:00:25Z",
        "robot_id": "CRUZR_01",
        "alert_id": "AlertEvent:SCN_CRITICAL_001",
        "zone_id": "DNTU_ROOM_A101",
        "action_type": "VOICE_DISPLAY_GUIDANCE",
        "navigation_mode": "PREDEFINED_RESPONSE_POINT",
        "message": "...",
        "status": "ACK"
    }
    """
    log_file = "logs/robot_actions.jsonl"
    os.makedirs("logs", exist_ok=True)
    
    log_entry = {
        "demo_run_id": os.getenv("DEMO_RUN_ID", "DNTU02_TOP8_RUN_2026_001"),
        "timestamp": _utc_now(),
        "robot_id": "CRUZR_01",
        "alert_id": alert_id,
        "zone_id": zone_id,
        "action_type": "VOICE_DISPLAY_GUIDANCE",
        "navigation_mode": "PREDEFINED_RESPONSE_POINT",
        "message": message,
        "status": status
    }
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    print(f"   📝 RobotAction log saved: {log_file}")
    return log_entry

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

def control_smart_plugs():
    """Điều khiển ổ cắm khi cháy: tắt a102/a103, bật a104 (1 kết nối, song song)."""
    print("\n🔌 Controlling smart plugs...")

    results = control_fire_emergency_plugs()
    for name, outcome in results.items():
        action = "ON" if name.endswith("a104") else "OFF"
        if outcome["success"]:
            print(f"   ✅ {name} turned {action}")
        else:
            err = outcome.get("error") or "unknown error"
            print(f"   ❌ {name} failed ({action}): {err}")

    print("\n🔌 Smart plugs control completed!")


def send_robot_emergency(temperature: float, smoke: int):
    """Gửi lệnh khẩn cấp đến robot (giữ kết nối)"""
    robot_client = get_robot()

  
    
    # Kết nối nếu chưa kết nối
    if not robot_client.is_connected():
        if not robot_client.connect():
            print(f"   ❌ Cannot connect to robot at {robot_client.ip}:{robot_client.port}")
            return False
    
    try:

        zone_id = os.getenv("ZONE_ID", "DNTU_ROOM_A101")
        alert_id = "AlertEvent:SCN_CRITICAL_001"
        message = f"⚠️ CẢNH BÁO CHÁY! Nhiệt độ {temperature} độ C! Vui lòng sơ tán khẩn cấp! ⚠️"
        
        # 1. GHI LOG ROBOTACTION (TRƯỚC KHI GỬI LỆNH)
        write_robot_action_log(
            alert_id=alert_id,
            zone_id=zone_id,
            message=message,
            status="DISPATCHED"
        )


          # 2. Di chuyển robot lên trước (ước lượng 2 mét)
        # Theo tài liệu: stream_move_input với direction="forward", speed=0.5
        # print(f"   🚶 Robot moving forward...")
       
        
        # Hiển thị emotion khẩn cấp
        result = robot_client.play_emotion("emotion://va/techface_upset")
        print(f"   😫 Emotion result: {result}")

        
        # robot.turn_left(speed=6)
        # time.sleep(6.2)
        # robot_client.stop()

        result = robot_client.speak(message)

        # robot_client.move_forward(speed=1)
        # time.sleep(3)  # Chạy 4 giây (speed=0.5 ~ 0.25 m/s → ~1m, cần test lại)
        # robot_client.stop()

        # robot.turn_right(speed=1)
        # time.sleep(0.5)


        # robot_client.stop()

        # control_smart_plugs()

        print(f"   ✅ Robot moved")
        
      
        
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