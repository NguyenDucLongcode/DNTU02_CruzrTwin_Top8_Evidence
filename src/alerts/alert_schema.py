import os
from src.common.time_utils import now_iso

def build_alert_event(ai_result: dict) -> dict:
    """
    Build an AlertEvent structure from the AI detection results.
    Only called if predicted_level is 'warning' or 'critical'.
    """
    level = ai_result.get("predicted_level", "warning")
    timestamp = ai_result.get("timestamp") or now_iso()
    
    if level == "critical":
        message = "Critical room problem found. Please send Cruzr guidance."
        rec_action = "DISPATCH_CRUZR_GUIDANCE"
    else:
        message = "Warning room problem found. Please check the room."
        rec_action = "CHECK_ROOM"
        
    return {
        "alert_id": f"AlertEvent:{timestamp}",
        "timestamp": timestamp,
        "level": level,
        "status": "OPEN",
        "source": "AI_DETECTION",
        "ai_result": ai_result,
        "recommended_action": rec_action,
        "message": message
    }
