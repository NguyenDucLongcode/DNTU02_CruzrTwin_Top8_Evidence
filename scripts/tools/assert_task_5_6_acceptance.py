import os
import sys
import json

# Ensure project root is in path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.common.config import get_config

def main():
    config = get_config()
    summary_path = os.path.join(config["evidence_dir"], "task_5_6_test_summary.json")
    
    print("=" * 60)
    print("RUNNING ACCEPTANCE ASSERTIONS...")
    print("=" * 60)
    
    if not os.path.exists(summary_path):
        print(f"FAIL: Test summary file not found at {summary_path}. Run scripts/demo/run_task_5_6_demo.py first.")
        sys.exit(1)
        
    try:
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
            
        cases = summary.get("cases", {})
        passed = True
        
        # 1. Normal case assertions
        normal = cases.get("normal", {})
        if normal.get("predicted_level") == "normal" and not normal.get("alert_created"):
            print("-> Normal case: PASS (No alert generated)")
        else:
            print(f"-> Normal case: FAIL (Level={normal.get('predicted_level')}, AlertCreated={normal.get('alert_created')})")
            passed = False
            
        # 2. Warning case assertions
        warning = cases.get("warning", {})
        if warning.get("predicted_level") == "warning" and warning.get("alert_created") and warning.get("alert_level") == "warning":
            print("-> Warning case: PASS (Warning alert generated)")
        else:
            print(f"-> Warning case: FAIL (Level={warning.get('predicted_level')}, AlertCreated={warning.get('alert_created')}, AlertLevel={warning.get('alert_level')})")
            passed = False
            
        # 3. Critical case assertions
        critical = cases.get("critical", {})
        if critical.get("predicted_level") == "critical" and critical.get("alert_created") and critical.get("alert_level") == "critical":
            print("-> Critical case: PASS (Critical alert generated)")
        else:
            print(f"-> Critical case: FAIL (Level={critical.get('predicted_level')}, AlertCreated={critical.get('alert_created')}, AlertLevel={critical.get('alert_level')})")
            passed = False
            
        print("=" * 60)
        if passed:
            print("OVERALL ACCEPTANCE: PASS")
            print("=" * 60)
            sys.exit(0)
        else:
            print("OVERALL ACCEPTANCE: FAIL")
            print("=" * 60)
            sys.exit(1)
            
    except Exception as e:
        print(f"FAIL: Error reading summary file: {e}")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
