import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from src.utils.mqtt_helper import publish_scenario

# ======================================================
# DỮ LIỆU WARNING (THEO FILE WORD)
# ======================================================

WARNING_VALUES = {
    "temp_sensor_a101": 32.0,      # °C
    "humid_sensor_a101": 65.0,     # %
    "air_sensor_a101": 1100,       # ppm
    "smoke_sensor_a101": 0,        # binary
    "smart_plug_a101": 680         # W
}

# ======================================================
# MAIN
# ======================================================

if __name__ == "__main__":
    publish_scenario(
        device_values=WARNING_VALUES,
        scenario_name="🟡 RUNNING WARNING SCENARIO (MQTT)",
        scenario_id_param="SCN_WARNING_001"
    )