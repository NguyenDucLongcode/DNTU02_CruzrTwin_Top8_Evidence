import os
import sys

# Ensure project root is in path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.ai.data_generator import generate_dataset
from src.common.config import get_config

def main():
    config = get_config()
    out_path = config["data_path"]
    
    result = generate_dataset(out_path)
    
    print("Data created.")
    print(f"Path: {result['output_path']}")
    print(f"Normal rows: {result['normal_rows']}")
    print(f"Anomaly rows: {result['anomaly_rows']}")
    print(f"Total rows: {result['total_rows']}")

if __name__ == "__main__":
    main()
