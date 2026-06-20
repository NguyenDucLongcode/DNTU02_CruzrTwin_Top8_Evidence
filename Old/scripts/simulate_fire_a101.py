import time
import sys
import os

# Thêm đường dẫn gốc vào PYTHONPATH để import mqtt_helper
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.mqtt_helper import publish_scenario

def simulate_fire():
    print("BAT DAU MO PHONG VU CHAY (BAN QUA MQTT VAO HE THONG FIWARE)")
    try:
        # GIAI ĐOẠN 1
        print("\n--- GIAI DOAN 1: Khoi phat chay tai A101 ---")
        publish_scenario({
            "temp_sensor_a101": 45.5,
            "smoke_sensor_a101": 35.0,
            "air_sensor_a101": 800
        }, scenario_name="FIRE_PHASE_1", scenario_id="SCN_SIMULATED_1")
        time.sleep(4)
        
        # GIAI ĐOẠN 2
        print("\n--- GIAI DOAN 2: Lua bung phat du doi tai A101, khoi tran sang A102 ---")
        publish_scenario({
            "temp_sensor_a101": 75.0,
            "smoke_sensor_a101": 80.0,
            "air_sensor_a101": 1500,
            "temp_sensor_a102": 30.0,
            "smoke_sensor_a102": 15.0,
            "air_sensor_a102": 600
        }, scenario_name="FIRE_PHASE_2", scenario_id="SCN_SIMULATED_2")
        time.sleep(4)
        
        # GIAI ĐOẠN 3
        print("\n--- GIAI DOAN 3: Lua lan sang A102, khoi lan den A103, A104 ---")
        publish_scenario({
            "temp_sensor_a101": 85.0, "smoke_sensor_a101": 95.0, "air_sensor_a101": 1500,
            "temp_sensor_a102": 55.0, "smoke_sensor_a102": 60.0, "air_sensor_a102": 900,
            "temp_sensor_a103": 35.0, "smoke_sensor_a103": 30.0, "air_sensor_a103": 700,
            "temp_sensor_a104": 30.0, "smoke_sensor_a104": 20.0, "air_sensor_a104": 600
        }, scenario_name="FIRE_PHASE_3", scenario_id="SCN_SIMULATED_3")
        time.sleep(4)
        
        # GIAI ĐOẠN 4
        print("\n--- GIAI DOAN 4: Chay lon, lan ra nua day nha (A101 -> A105) ---")
        publish_scenario({
            "temp_sensor_a101": 95.0, "smoke_sensor_a101": 98.0, "air_sensor_a101": 1500,
            "temp_sensor_a102": 80.0, "smoke_sensor_a102": 85.0, "air_sensor_a102": 1200,
            "temp_sensor_a103": 60.0, "smoke_sensor_a103": 65.0, "air_sensor_a103": 1000,
            "temp_sensor_a104": 45.0, "smoke_sensor_a104": 45.0, "air_sensor_a104": 800,
            "temp_sensor_a105": 35.0, "smoke_sensor_a105": 35.0, "air_sensor_a105": 700,
            "temp_sensor_a106": 30.0, "smoke_sensor_a106": 25.0, "air_sensor_a106": 600
        }, scenario_name="FIRE_PHASE_4", scenario_id="SCN_SIMULATED_4")
        
        print("\n MO PHONG HOAN TAT. GIAO DIEN SE TU DONG CAP NHAT QUA DB!")
        
    except KeyboardInterrupt:
        print("\nNgung mo phong.")

if __name__ == "__main__":
    simulate_fire()
