"""
Webhook Receiver - Nhận notification từ Orion
- Cập nhật Room entity khi có dữ liệu mới
- Ghi log xác nhận webhook đã hoạt động
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
from src.fiware.entities.query import get_room_state, get_all_devices, get_entity_by_type

app = Flask(__name__)

# File log đơn giản
LOG_FILE = "logs/webhook_notifications.jsonl"


@app.route('/webhook/notify', methods=['POST'])
def webhook_notify():
    """Nhận notification từ Orion, cập nhật Room và ghi log"""
    
    data = request.json
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    
    print("\n" + "=" * 60)
    print(f" [{timestamp}] Webhook received from Orion!")
    print("=" * 60)
    
    # Trích xuất dữ liệu
    if 'data' in data and len(data['data']) > 0:
        entity = data['data'][0]

        tracked_attrs = [
            "temperature",
            "humidity",
            "co2",
            "smoke_status",
            "energy_consumption",
        ]

        

        # Chỉ cập nhật attrs thực sự có trong notification để tránh ghi đè stale value.
        changed_sensor_data = {}
        for key in tracked_attrs:
            if key in entity:
                v = entity[key]
                if isinstance(v, dict) and "value" in v:
                    changed_sensor_data[key] = v["value"]
                else:
                    changed_sensor_data[key] = v

        # Lấy các giá trị cảm biến (chuẩn hoá cho việc in log)
        sensor_data = {}
        for key in tracked_attrs:
            v = entity.get(key, "N/A")
            if isinstance(v, dict) and "value" in v:
                sensor_data[key] = v["value"]
            else:
                sensor_data[key] = v
        
        # In ra console
        print(f"\n📊 Received sensor data:")
        print(f"   Temperature: {sensor_data['temperature']}°C")
        print(f"   Humidity: {sensor_data['humidity']}%")
        print(f"   CO2: {sensor_data['co2']} ppm")
        print(f"   Smoke: {sensor_data['smoke_status']}")
        print(f"   Energy: {sensor_data['energy_consumption']}W")
        
        # ==================================================
        # CẬP NHẬT ROOM ENTITY
        # ==================================================
        print(f"\n Updating Room entity...")
        if changed_sensor_data and update_room_sensors(changed_sensor_data):
            print(f"  Room entity updated successfully!")
            # --- Khi Room được cập nhật thành công, ghi snapshot trạng thái Orion ---
            try:
                os.makedirs("logs", exist_ok=True)
                snapshot = {
                    "timestamp": timestamp,
                    "room": get_room_state() or {},
                    "devices": get_all_devices() or [],
                    "alerts": get_entity_by_type("AlertEvent") or [],
                    "robot_actions": get_entity_by_type("RobotAction") or [],
                }
                with open("logs/orion_state.jsonl", "a", encoding="utf-8") as sf:
                    sf.write(json.dumps(snapshot, ensure_ascii=False) + "\n")
                print("  Orion state snapshot appended: logs/orion_state.jsonl")
            except Exception as e:
                print(f"  ⚠️ Failed to write Orion snapshot: {e}")
        elif not changed_sensor_data:
            print(f"   ⚠️ No tracked sensor attrs in payload")
        else:
            print(f"   ⚠️ Failed to update Room entity")
        
        # ==================================================
        # GHI LOG WEBHOOK NHẬN ĐƯỢC
        # ==================================================
        log_entry = {
            "timestamp": timestamp,
            "status": "webhook_received",
            "entity_id": entity.get("id", "unknown"),
            "sensor_data": sensor_data,
            "changed_sensor_data": changed_sensor_data
        }
        
        os.makedirs("logs", exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        
        print(f"\n Webhook log saved: {LOG_FILE}")
    
    else:
        print("   No data in webhook payload")
    
    print("=" * 60)
    
    return jsonify({"status": "ok", "message": "Webhook received"}), 200


@app.route('/webhook/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Webhook Receiver",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }, 200


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🔔 Webhook Receiver - Ready")
    print("=" * 60)
    print(f"   URL: http://0.0.0.0:5000/webhook/notify")
    print(f"   Health: http://0.0.0.0:5000/webhook/health")
    print("   Waiting for Orion notifications...")
    print("=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)