import os
import sys

# Ensure project root is in path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.ai.data_loader import load_sensor_data, validate_sensor_data
from src.common.config import get_config
from src.common.errors import ValidationError

def main():
    config = get_config()
    csv_path = config["data_path"]
    
    print("=" * 60)
    print("VALIDATING SENSOR DATA CSV...")
    print("=" * 60)
    
    if not os.path.exists(csv_path):
        print(f"FAIL: Sensor data CSV not found at {csv_path}")
        sys.exit(1)
        
    try:
        df = load_sensor_data(csv_path)
        stats = validate_sensor_data(df)
        print("PASS: Sensor data is valid.")
        print(f"  Total Rows:  {stats['eval_rows']}")
        print(f"  Normal Rows: {stats['normal_rows']}")
        print(f"  Anomaly Rows:{stats['anomaly_rows']}")
        print("=" * 60)
        sys.exit(0)
    except ValidationError as ve:
        print(f"FAIL: Data validation failed: {ve}")
        print("=" * 60)
        sys.exit(1)
    except Exception as e:
        print(f"FAIL: Unexpected error during validation: {e}")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
