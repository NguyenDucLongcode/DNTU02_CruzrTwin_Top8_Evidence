import os
from src.alerts.alert_schema import build_alert_event
from src.common import config
from src.common.logging_utils import append_jsonl

def create_alert_event(ai_result: dict) -> dict | None:
    """
    Process AI detection result and create an AlertEvent if warning or critical.
    Logs the event to alert_events.jsonl.
    """
    if ai_result.get("predicted_level") == "normal":
        return None
        
    # Build full alert event dict
    event = build_alert_event(ai_result)
    
    # Construct log entry with requested ai_result_ref schema
    log_entry = {
        "timestamp": event["timestamp"],
        "alert_id": event["alert_id"],
        "level": event["level"],
        "status": event["status"],
        "source": event["source"],
        "recommended_action": event["recommended_action"],
        "message": event["message"],
        "ai_result_ref": {
            "predicted_anomaly": int(ai_result.get("predicted_anomaly", 0)),
            "predicted_level": ai_result.get("predicted_level"),
            "anomaly_score": float(ai_result.get("anomaly_score", 0.0))
        }
    }
    
    # Log to logs/alert_events.jsonl
    cfg = config.get_config()
    alert_log_path = os.path.join(cfg["log_dir"], "alert_events.jsonl")
    append_jsonl(alert_log_path, log_entry)
    
    return event
