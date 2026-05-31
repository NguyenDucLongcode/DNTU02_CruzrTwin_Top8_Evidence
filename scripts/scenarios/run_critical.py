import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from src.utils.mqtt_helper import publish_scenario

# ======================================================
# DỮ LIỆU CRITICAL (THEO FILE WORD)
# ======================================================

CRITICAL_VALUES = {
    "temp_sensor_a101": 39.8,      # °C
    "humid_sensor_a101": 78.0,     # %
    "air_sensor_a101": 1250,       # ppm
    "smoke_sensor_a101": 1,        # binary ← CÓ KHÓI
    "smart_plug_a101": 920         # W
}

# ======================================================
# MAIN
# ======================================================

if __name__ == "__main__":
    print("\n   🔥🔥🔥 SMOKE DETECTED! 🔥🔥🔥")
    
    publish_scenario(
        device_values=CRITICAL_VALUES,
        scenario_name="🔴 RUNNING CRITICAL SCENARIO (MQTT)",
        scenario_id_param="SCN_CRITICAL_001"
    )
    
    print("   🚨 Robot should be dispatched! 🚨")