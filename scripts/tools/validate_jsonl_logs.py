import os
import sys
import json

# Ensure project root is in path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.common.config import get_config

def check_jsonl(path: str) -> bool:
    if not os.path.exists(path):
        print(f"-> {os.path.basename(path)}: FAIL (File not found)")
        return False
        
    try:
        count = 0
        with open(path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                json.loads(line)
                count += 1
        print(f"-> {os.path.basename(path)}: PASS ({count} valid JSON lines)")
        return True
    except Exception as e:
        print(f"-> {os.path.basename(path)}: FAIL (Line {line_num} error: {e})")
        return False

def main():
    config = get_config()
    
    passed = True
    print("=" * 60)
    print("VALIDATING JSONL LOGS...")
    print("=" * 60)
    
    # Check ai_detection.jsonl
    ai_log = os.path.join(config["log_dir"], "ai_detection.jsonl")
    if not check_jsonl(ai_log):
        passed = False
        
    # Check alert_events.jsonl (if exists)
    alert_log = os.path.join(config["log_dir"], "alert_events.jsonl")
    if os.path.exists(alert_log):
        if not check_jsonl(alert_log):
            passed = False
    else:
        print(f"-> alert_events.jsonl: SKIP (Does not exist yet)")
        
    print("=" * 60)
    if passed:
        print("OVERALL RESULT: PASS")
        print("=" * 60)
        sys.exit(0)
    else:
        print("OVERALL RESULT: FAIL")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
