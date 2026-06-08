from src.ai.detector import detect_anomaly
from src.alerts.alert_service import create_alert_event

def process_sensor_event(sensor: dict) -> dict:
    """
    Orchestrate the processing of a single sensor reading event.
    Returns a dictionary containing:
    - ai_result: result from the AI detector
    - alert_event: created AlertEvent dictionary (or None if normal)
    """
    ai_result = detect_anomaly(sensor)
    alert_event = create_alert_event(ai_result)
    
    return {
        "ai_result": ai_result,
        "alert_event": alert_event
    }
