"""
Webhook Receiver - Nhận notification từ Orion
- Cập nhật Room entity khi có dữ liệu mới
- Kích hoạt Orchestration Pipeline để chạy closed-loop
"""

import json
import os
import sys
from datetime import datetime, timezone
from flask import Flask, request, jsonify

# Thêm đường dẫn để import
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from src.fiware.entities import update_room_sensors, get_room_state
from src.orchestration.event_pipeline import process_room_state

app = Flask(__name__)

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def _extract_value(value):
    if isinstance(value, dict) and "value" in value:
        return value["value"]
    return value

@app.route('/webhook/notify', methods=['POST'])
def webhook_notify():
    """Nhận notification từ Orion, cập nhật Room và kích hoạt Orchestration"""
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

    # Cập nhật Room entity và kích hoạt closed-loop pipeline
    if changed_sensor_data:
        update_room_sensors(changed_sensor_data)
        
        # Lấy Room state từ Orion (chứa tất cả sensors) để chạy AI
        room_state = get_room_state()
        if room_state:
            # Gửi sang pipeline orchestration để xử lý
            process_room_state(room_state)

    return jsonify({"status": "ok"}), 200

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