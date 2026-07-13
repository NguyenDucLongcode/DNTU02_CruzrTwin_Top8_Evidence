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
    
    ai_log = os.path.join(config["log_dir"], "ai_detection.jsonl")
    alert_log = os.path.join(config["log_dir"], "alert_events.jsonl")
    
    print("=" * 60)
    print("SHOWING TASK 5-6 PIPELINE TRACE...")
    print("=" * 60)
    
    if not os.path.exists(ai_log):
        print("No AI detection log found. Please run evaluation or demo first.")
        sys.exit(1)
        
    # Read AI detections
    detections = []
    with open(ai_log, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                detections.append(json.loads(line))
                
    # Read Alerts
    alerts = {}
    if os.path.exists(alert_log):
        with open(alert_log, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    alert = json.loads(line)
                    # Key by timestamp
                    alerts[alert["timestamp"]] = alert
                    
    # Display recent 10 detections and their alerts
    recent_detections = detections[-10:]
    for det in recent_detections:
        ts = det["timestamp"]
        lvl = det["predicted_level"]
        score = det["anomaly_score"]
        
        print(f"[{ts}] AI Level: {lvl.upper()} | Score: {score:.4f}")
        
        if lvl in ["warning", "critical"]:
            # Check if alert exists
            alert = alerts.get(ts)
            if alert:
                print(f"  +- [ALERT] Event: {alert['alert_id']}")
                print(f"     Status: {alert['status']} | Msg: \"{alert['message']}\"")
                print(f"     Action: {alert['recommended_action']}")
            else:
                print(f"  +- [ALERT] Event: (Alert not found for this timestamp)")
        else:
            print("  +- (Normal: No Alert Event created)")
            
    print("=" * 60)

if __name__ == "__main__":
    main()
