import os
import sys
import shutil
# Add project root to path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from src.common.config import LOG_DIR

def reset_logs():
    print(f"Resetting log files in: {LOG_DIR} ...")
    if os.path.exists(LOG_DIR):
        for filename in os.listdir(LOG_DIR):
            file_path = os.path.join(LOG_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
                
    os.makedirs(LOG_DIR, exist_ok=True)
    # create placeholder for orion sync
    open(os.path.join(LOG_DIR, "orion_sync.jsonl"), "w").close()
    print("Logs successfully reset.")

if __name__ == "__main__":
    reset_logs()
