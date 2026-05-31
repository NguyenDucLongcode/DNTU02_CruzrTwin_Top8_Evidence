
"""
MỤC ĐÍCH:
- Tạo 30 file JSON test (10 normal, 10 warning, 10 critical)
- Dữ liệu theo đúng yêu cầu file Word


MỖI FILE CÓ:
- scenario_id: tên file
- expected_label: normal/warning/critical
- zone_id: DNTU_ROOM_A101
- demo_run_id: DNTU02_TOP8_RUN_2026_001
- readings: 4 readings (t=0,10,20,30)
"""

import json
import os
import random
from pathlib import Path

# ======================================================
# CẤU HÌNH
# ======================================================

DEMO_RUN_ID = "DNTU02_TOP8_RUN_2026_001"
ZONE_ID = "DNTU_ROOM_A101"
OUTPUT_DIR = Path("data/replay_test_set")

# ======================================================
# GIÁ TRỊ THEO FILE WORD
# ======================================================

# Giá trị normal (ổn định)
NORMAL_VALUES = {
    "temperature": (24.0, 26.0),
    "humidity": (53.0, 57.0),
    "co2": (410, 430),
    "smoke": 0,
    "energy": (340, 360)
}

# Giá trị warning (cảnh báo - tăng dần)
WARNING_VALUES = {
    "temperature": (28.0, 32.0),
    "humidity": (58.0, 65.0),
    "co2": (800, 1100),
    "smoke": 0,
    "energy": (500, 680)
}

# Giá trị critical (nguy hiểm)
CRITICAL_VALUES = {
    "temperature": (32.0, 39.8),
    "humidity": (65.0, 78.0),
    "co2": (800, 1250),
    "smoke": (0, 1),  # smoke xuất hiện ở cuối
    "energy": (500, 920)
}


# ======================================================
# HÀM TẠO READING
# ======================================================

def generate_reading(values_config: dict, step: int, total_steps: int = 4) -> dict:
    """
    Tạo 1 reading dựa trên step (tiến trình)
    """
    progress = step / total_steps  # 0 → 1
    
    # Temperature
    temp_min, temp_max = values_config["temperature"]
    temperature = round(temp_min + (temp_max - temp_min) * progress + random.uniform(-0.3, 0.3), 1)
    
    # Humidity
    hum_min, hum_max = values_config["humidity"]
    humidity = round(hum_min + (hum_max - hum_min) * progress + random.uniform(-0.5, 0.5), 1)
    
    # CO2
    co2_min, co2_max = values_config["co2"]
    co2 = int(co2_min + (co2_max - co2_min) * progress + random.randint(-10, 10))
    
    # Smoke (chỉ xuất hiện ở cuối critical)
    smoke_config = values_config["smoke"]
    if isinstance(smoke_config, tuple):
        # smoke xuất hiện khi progress > 0.7
        smoke = 1 if smoke_config[1] == 1 and progress > 0.7 else 0
    else:
        smoke = smoke_config
    
    # Energy
    energy_min, energy_max = values_config["energy"]
    energy = int(energy_min + (energy_max - energy_min) * progress + random.randint(-10, 10))
    
    return {
        "t": step * 10,  # giây
        "temperature": temperature,
        "humidity": humidity,
        "co2": co2,
        "smoke_status": smoke,
        "energy_consumption": energy
    }


# ======================================================
# TẠO FILE TEST
# ======================================================

def create_test_file(scenario_id: str, expected_label: str, values_config: dict, num_readings: int = 4) -> dict:
    """
    Tạo 1 file test JSON hoàn chỉnh
    """
    readings = []
    for step in range(num_readings):
        reading = generate_reading(values_config, step, num_readings)
        readings.append(reading)
    
    return {
        "scenario_id": scenario_id,
        "expected_label": expected_label,
        "zone_id": ZONE_ID,
        "demo_run_id": DEMO_RUN_ID,
        "readings": readings
    }


# ======================================================
# TẠO 30 FILE
# ======================================================

def generate_all_test_files():
    """
    Tạo 30 file test
    - 10 normal
    - 10 warning
    - 10 critical
    """
    
    # Tạo thư mục
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "=" * 60)
    print(" GENERATING REPLAY TEST FILES")
    print("=" * 60)
    print(f"   Output: {OUTPUT_DIR}")
    print(f"   Total : 30 files (10 normal, 10 warning, 10 critical)")
    print("-" * 60)
    
    # ==============================================
    # NORMAL (10 files)
    # ==============================================
    for i in range(1, 11):
        scenario_id = f"normal_{i:03d}"
        test_data = create_test_file(scenario_id, "normal", NORMAL_VALUES)
        
        file_path = OUTPUT_DIR / f"{scenario_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(test_data, f, indent=2)
        
        print(f"  Created: {scenario_id}.json")
    
    # ==============================================
    # WARNING (10 files)
    # ==============================================
    for i in range(1, 11):
        scenario_id = f"warning_{i:03d}"
        test_data = create_test_file(scenario_id, "warning", WARNING_VALUES)
        
        file_path = OUTPUT_DIR / f"{scenario_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(test_data, f, indent=2)
        
        print(f"  Created: {scenario_id}.json")
    
    # ==============================================
    # CRITICAL (10 files)
    # ==============================================
    for i in range(1, 11):
        scenario_id = f"critical_{i:03d}"
        test_data = create_test_file(scenario_id, "critical", CRITICAL_VALUES)
        
        file_path = OUTPUT_DIR / f"{scenario_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(test_data, f, indent=2)
        
        print(f"   Created: {scenario_id}.json")
    
    print("-" * 60)
    print(f"Total: 30 files created successfully!")
    print("=" * 60)


# ======================================================
# MAIN
# ======================================================

if __name__ == "__main__":
    generate_all_test_files()