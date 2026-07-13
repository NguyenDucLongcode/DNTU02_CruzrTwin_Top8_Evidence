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
    
    passed = True
    print("=" * 60)
    print("VALIDATING AI EVIDENCE FILES...")
    print("=" * 60)
    
    # Check 1: Models
    model_path = config["model_path"]
    if os.path.exists(model_path):
        print(f"-> check anomaly_model.pkl: PASS")
    else:
        print(f"-> check anomaly_model.pkl: FAIL (Not found at {model_path})")
        passed = False
        
    schema_path = config["feature_schema_path"]
    if os.path.exists(schema_path):
        print(f"-> check feature_schema.json: PASS")
    else:
        print(f"-> check feature_schema.json: FAIL (Not found at {schema_path})")
        passed = False
        
    # Check 2: Summaries
    summary_path = os.path.join(config["evidence_dir"], "training_summary.json")
    if os.path.exists(summary_path):
        print(f"-> check training_summary.json: PASS")
        # Validate constraint
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            anomaly_rows = data.get("anomaly_rows_used_for_training", -1)
            if anomaly_rows == 0:
                print("   -> training uses label 0 only: PASS")
            else:
                print(f"   -> training uses label 0 only: FAIL (anomaly_rows_used_for_training was {anomaly_rows}, expected 0)")
                passed = False
        except Exception as e:
            print(f"   -> read training_summary.json error: FAIL ({e})")
            passed = False
    else:
        print(f"-> check training_summary.json: FAIL (Not found)")
        passed = False
        
    # Check 3: Metrics
    metrics_path = os.path.join(config["evidence_dir"], "ai_metrics.json")
    if os.path.exists(metrics_path):
        print(f"-> check ai_metrics.json: PASS")
    else:
        print(f"-> check ai_metrics.json: FAIL (Not found)")
        passed = False
        
    # Check 4: Detection Logs
    det_log_path = os.path.join(config["log_dir"], "ai_detection.jsonl")
    if os.path.exists(det_log_path):
        print(f"-> check ai_detection.jsonl: PASS")
    else:
        print(f"-> check ai_detection.jsonl: FAIL (Not found)")
        passed = False
        
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
