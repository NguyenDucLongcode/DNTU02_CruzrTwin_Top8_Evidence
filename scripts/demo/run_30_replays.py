import os
import sys
import time
from pathlib import Path

# Ensure project root is in path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.utils.mqtt_helper import create_mqtt_client, disconnect_mqtt_client, publish_scenario_with_client
from src.utils.replay_helpers import (
    load_test_file,
    extract_all_readings,
    extract_device_values_from_reading,
    build_scenario_id,
)

# ======================================================
# ĐƯỜNG DẪN FILE TEST
# ======================================================
TEST_DIR = Path(os.getenv("TEST_DIR", os.path.join(ROOT_DIR, "data", "replay_test_set")))

FILES_TO_RUN = [
    "normal_001.json",
    "warning_001.json",
    "critical_001.json"
]

def run_30_replays():
    mqtt_client = create_mqtt_client()
    if not mqtt_client:
        print("❌ Lỗi: Không thể khởi tạo MQTT client.")
        return

    delay_between_readings = 0.05
    
    try:
        for file_name in FILES_TO_RUN:
            file_path = TEST_DIR / file_name
            test_data = load_test_file(file_path)
            if not test_data:
                print(f"❌ Không thể đọc file: {file_path}")
                continue
            
            readings = extract_all_readings(test_data)
            base_scenario_id = build_scenario_id(file_name)
            
            print(f"\n🚀 Bắt đầu gửi 30 replays cho file: {file_name}")
            print(f"📊 Số readings mỗi replay: {len(readings)}")
            print("=" * 60)
            
            run_timestamp = int(time.time())
            
            for iter_idx in range(1, 31):
                scenario_id = f"{base_scenario_id}_T{run_timestamp}_ITER_{iter_idx}"
                scenario_name = f"REPLAY {scenario_id}"
                
                print(f"   📤 Đang gửi vòng lặp {iter_idx}/30 ({scenario_id})...")
                
                for r_idx, reading in enumerate(readings, 1):
                    device_values = extract_device_values_from_reading(reading)
                    
                    publish_scenario_with_client(
                        client=mqtt_client,
                        device_values=device_values,
                        scenario_name=scenario_name,
                        scenario_id=scenario_id,
                    )
                    
                    if r_idx < len(readings):
                        time.sleep(delay_between_readings)
                
                time.sleep(0.1)
                
        print("\n✅ Đã gửi thành công toàn bộ 90 replays qua MQTT!")
        
    except Exception as e:
        print(f"❌ Lỗi trong quá trình chạy replay: {e}")
    finally:
        disconnect_mqtt_client(mqtt_client)

if __name__ == "__main__":
    for f in ["sensorReading.jsonl", "ai_detection.jsonl", "alert_events.jsonl", "robot_actions.jsonl"]:
        p = os.path.join(ROOT_DIR, "logs", f)
        if os.path.exists(p):
            try:
                os.remove(p)
            except:
                pass
                
    print("\n" + "=" * 60)
    print("🚀 CHẠY 30 REPLAYS QUA MQTT CHO TỪNG SCENARIO")
    print("=" * 60)
    
    run_30_replays()
