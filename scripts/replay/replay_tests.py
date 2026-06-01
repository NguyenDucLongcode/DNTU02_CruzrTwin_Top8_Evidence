"""
========================================================
REPLAY TEST RUNNER - CHẠY LẠI CÁC KỊCH BẢN TEST
========================================================
"""

import os
import sys
import json
import time
import logging
from pathlib import Path

# Thêm đường dẫn gốc
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Import từ helper
from src.utils.mqtt_helper import (
    create_mqtt_client,
    disconnect_mqtt_client,
    publish_scenario_with_client,
)
from src.utils.replay_helpers import (
    load_test_files,
    extract_all_readings,
    extract_device_values_from_reading,
    build_scenario_id,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("replay_tests")


def send_file_readings(mqtt_client, file_path: Path, delay: float = 1.0):
    """
    Đọc 1 file test và gửi tuần tự từng reading
    
    Args:
        mqtt_client: MQTT client đã kết nối
        file_path: Đường dẫn file JSON
        delay: Thời gian delay giữa các reading (giây)
    """
    # Đọc file
    with open(file_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    
    # Lấy danh sách readings
    readings = extract_all_readings(payload)
    scenario_id = build_scenario_id(file_path.name)
    scenario_name = f"REPLAY {scenario_id}"
    
    logger.info(f"📁 File: {file_path.name} - {len(readings)} readings")
    
    # Gửi từng reading
    for i, reading in enumerate(readings, 1):
        t = reading.get("t", 0)
        device_values = extract_device_values_from_reading(reading)
        
        logger.info(f"   📤 Reading {i}/{len(readings)} (t={t}s)")
        logger.info(f"      Temp: {device_values['temp_sensor_a101']}°C, CO2: {device_values['air_sensor_a101']}ppm, Smoke: {device_values['smoke_sensor_a101']}")
        
        # Gửi dữ liệu
        publish_scenario_with_client(
            client=mqtt_client,
            device_values=device_values,
            scenario_name=scenario_name,
            scenario_id=scenario_id,
        )
        
        # Delay giữa các readings
        if i < len(readings):
            time.sleep(delay)


def run_all(test_dir: Path, fimat_url: str, out_log: Path, pause: float = 1.0):
    """Chạy tất cả các file test, mỗi file gửi tuần tự các readings"""
    
    files = load_test_files(test_dir)
    if not files:
        logger.error("Không tìm thấy file test nào trong %s", test_dir)
        return 1
    
    logger.info(f"📁 Tìm thấy {len(files)} file test")
    logger.info(f"⏱️  Delay giữa các readings: {pause}s")
    logger.info("=" * 60)
    
    # Tạo MQTT client một lần và tái sử dụng cho tất cả
    mqtt_client = create_mqtt_client()
    
    try:
        for i, file_path in enumerate(files, 1):
            logger.info(f"\n📄 [{i}/{len(files)}] Đang xử lý: {file_path.name}")
            
            # Gửi tuần tự các readings trong file
            send_file_readings(mqtt_client, file_path, delay=pause)
            
            # Nghỉ giữa các file (tùy chọn)
            if i < len(files):
                logger.info(f"   ⏳ Nghỉ {pause}s trước file tiếp theo...")
                time.sleep(pause)
        
        logger.info("\n✅ Replay hoàn tất!")
        return 0
        
    except Exception as e:
        logger.exception(f"❌ Lỗi: {e}")
        return 1
    finally:
        if mqtt_client:
            disconnect_mqtt_client(mqtt_client)


if __name__ == "__main__":
    test_dir = Path(os.getenv("TEST_DIR", "data/replay_test_set"))
    fimat_url = os.getenv("FIMAT_API_URL", "http://localhost:8080")
    out_log = Path(os.getenv("OUT_LOG", "logs/replay_results.jsonl"))
    
    exit(run_all(test_dir, fimat_url, out_log))