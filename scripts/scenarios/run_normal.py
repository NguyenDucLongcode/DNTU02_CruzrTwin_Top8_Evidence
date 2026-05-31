import os
import sys

# Thêm đường dẫn
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from src.utils.mqtt_helper import publish_scenario

# ======================================================
# DỮ LIỆU NORMAL (THEO FILE WORD)
# ======================================================

NORMAL_VALUES = {
    "temp_sensor_a101": 24.5,      # °C
    "humid_sensor_a101": 55.0,     # %
    "air_sensor_a101": 420,        # ppm
    "smoke_sensor_a101": 0,        # binary
    "smart_plug_a101": 350         # W
}

# ======================================================
# MAIN
# ======================================================

if __name__ == "__main__":
    publish_scenario(
        device_values=NORMAL_VALUES,
        scenario_name="🟢 RUNNING NORMAL SCENARIO (MQTT)",
        scenario_id_param="SCN_NORMAL_001"
    )