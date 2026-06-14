import os
import sys

# Ensure project root is in path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.ai.detector import detect_anomaly

def print_result(case_name, input_data):
    print(f"\n--- Testing {case_name} ---")
    print(f"Inputs: {input_data}")
    try:
        res = detect_anomaly(input_data)
        print(f"AI Predicted Anomaly: {res['predicted_anomaly']}")
        print(f"Severity level:       {res['predicted_level']}")
        print(f"Rationale:            \"{res['rationale']}\"")
        print(f"Recommended Action:   {res['recommended_action']}")
        print(f"Status:               {res['status']}")
    except Exception as e:
        print(f"ERROR running detector: {e}")

def main():
    print("=" * 60)
    print("TESTING MODEL DETECTION FUNCTIONALITIES")
    print("=" * 60)
    
    # 1. Normal sensor data
    normal_sensor = {
        "temperature": 25.0,
        "humidity": 60.0,
        "smoke": 50.0,
        "co2": 400.0,
        "power": 50.0
    }
    print_result("NORMAL CASE", normal_sensor)
    
    # 2. Warning sensor data
    warning_sensor = {
        "temperature": 34.0,
        "humidity": 65.0,
        "smoke": 180.0,
        "co2": 750.0,
        "power": 90.0
    }
    print_result("WARNING CASE", warning_sensor)
    
    # 3. Critical sensor data
    critical_sensor = {
        "temperature": 45.0,
        "humidity": 15.0,
        "smoke": 400.0,
        "co2": 1000.0,
        "power": 8.0
    }
    print_result("CRITICAL CASE", critical_sensor)
    print("=" * 60)

if __name__ == "__main__":
    main()
