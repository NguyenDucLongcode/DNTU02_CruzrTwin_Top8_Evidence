import os
import sys
import time
from pathlib import Path

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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

TEST_DIR = Path(os.getenv("TEST_DIR", "data/replay_test_set"))
FILE_NAME = "normal_001.json"
FILE_PATH = TEST_DIR / FILE_NAME

# ======================================================
# GỬI TỪNG READING
# ======================================================

def send_all_readings(file_path: Path, delay: float = 1.0):
    """Đọc file test và gửi tuần tự từng reading"""
    
    test_data = load_test_file(file_path)
    if not test_data:
        print(f"❌ Không thể đọc file: {file_path}")
        return False
    
    readings = extract_all_readings(test_data)
    scenario_id = build_scenario_id(file_path.name)
    scenario_name = f"REPLAY {scenario_id}"
    
    print(f"\n📁 File: {file_path.name}")
    print(f"📊 Số readings: {len(readings)}")
    print(f"⏱️  Delay: {delay}s giữa các readings")
    print("=" * 60)
    
    mqtt_client = create_mqtt_client()
    
    try:
        for i, reading in enumerate(readings, 1):
            t = reading.get("t", 0)
            device_values = extract_device_values_from_reading(reading)
            
            print(f"\n📤 Reading {i}/{len(readings)} (t={t}s)")
            print(f"   Temperature: {device_values['temp_sensor_a101']}°C")
            print(f"   CO2: {device_values['air_sensor_a101']} ppm")
            print(f"   Smoke: {device_values['smoke_sensor_a101']}")
             
          
            publish_scenario_with_client(
                client=mqtt_client,
                device_values=device_values,
                scenario_name=scenario_name,
                scenario_id=scenario_id,
            )
            
            if i < len(readings):
                time.sleep(delay)
        
        print("\n✅ Đã gửi tất cả readings thành công!")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return False
    finally:
        disconnect_mqtt_client(mqtt_client)


# ======================================================
# MAIN
# ======================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🟢 NORMAL SCENARIO")
    print("=" * 60)
    
    send_all_readings(FILE_PATH, delay=1.0)