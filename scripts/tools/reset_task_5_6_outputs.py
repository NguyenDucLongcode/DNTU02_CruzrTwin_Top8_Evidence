import os
import sys

# Ensure project root is in path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.common.config import get_config
from src.common.logging_utils import reset_file

def main():
    config = get_config()
    
    files_to_reset = [
        os.path.join(config["log_dir"], "ai_detection.jsonl"),
        os.path.join(config["log_dir"], "alert_events.jsonl"),
        os.path.join(config["log_dir"], "robot_actions.jsonl"),
        os.path.join(config["log_dir"], "sensor_readings.jsonl"),
        os.path.join(config["log_dir"], "orion_state.jsonl"),
        os.path.join(config["evidence_dir"], "task_5_6_test_summary.json"),
        os.path.join(config["evidence_dir"], "task_5_6_trace_sample.json")
    ]
    
    print("=" * 60)
    print("RESETTING TASK 5-6 OUTPUTS...")
    print("=" * 60)
    
    for f in files_to_reset:
        try:
            if os.path.exists(f):
                os.remove(f)
                print(f"Removed: {f}")
            else:
                print(f"File did not exist: {f}")
        except Exception as e:
            print(f"Error resetting {f}: {e}")
            
    print("=" * 60)
    print("RESET COMPLETED.")
    print("=" * 60)

if __name__ == "__main__":
    main()
