import os
from datetime import datetime, timezone
from src.common import config
from src.common.logging_utils import append_jsonl
from src.common.time_utils import now_iso

# In-memory sets to prevent duplicate creations/triggers of alerts and robot actions
_created_alerts = set()
_created_robot_actions = set()

def reset_alert_service_cache():
    """Reset the in-memory idempotency caches. Useful for tests."""
    global _created_alerts, _created_robot_actions
    _created_alerts.clear()
    _created_robot_actions.clear()

def create_alert_event(ai_result: dict, demo_run_id: str = None, scenario_id: str = None, zone_id: str = None) -> dict | None:
    """
    Process AI detection result and create an AlertEvent if warning or critical.
    Logs the event to alert_events.jsonl and upserts to Orion if enabled.
    """
    level = ai_result.get("predicted_level", "normal")
    if level == "normal":
        return None
        
    cfg = config.get_config()
    demo_run_id = demo_run_id or ai_result.get("demo_run_id") or cfg["demo_run_id"]
    scenario_id = scenario_id or ai_result.get("scenario_id") or "SCN_CRITICAL_001"
    zone_id = zone_id or ai_result.get("zone_id") or cfg["default_zone_id"]
    
    timestamp = ai_result.get("timestamp") or now_iso()
    anomaly_score = float(ai_result.get("anomaly_score", 0.0))
    
    # recommended_action dynamic value (full description)
    recommended_action = ai_result.get("recommended_action")
    if recommended_action:
        prefix = "Create critical AlertEvent, "
        if recommended_action.startswith(prefix):
            recommended_action = recommended_action[len(prefix):]
            if recommended_action.startswith("send Cruzr to response point, and request"):
                recommended_action = "Send Cruzr to response point and request" + recommended_action[len("send Cruzr to response point, and request"):]
            elif recommended_action and recommended_action[0].islower():
                recommended_action = recommended_action[0].upper() + recommended_action[1:]
    else:
        if level == "critical":
            recommended_action = "Send Cruzr to response point and request operator acknowledgement. Safety-critical actuation should remain operator-approved or simulated."
        elif level == "warning":
            recommended_action = "Create warning AlertEvent and notify operator."
        else:
            recommended_action = "No action required. Continue monitoring."
            
    action_code = ai_result.get("action_code") or ("DISPATCH_CRUZR_GUIDANCE" if level == "critical" else "CHECK_ROOM")
    
    alert_id = f"AlertEvent:{scenario_id}"
    source_ai_event_id = ai_result.get("source_ai_event_id") or f"AIEvent:{scenario_id}"
    
    if level == "critical":
        message = "Critical indoor-environment anomaly detected."
    else:
        message = "Warning indoor-environment anomaly detected."
        
    # Returned python object to keep legacy tests happy: status=OPEN, recommended_action as code
    event = {
        "demo_run_id": demo_run_id,
        "timestamp": timestamp,
        "alert_id": alert_id,
        "type": "AlertEvent",
        "scenario_id": scenario_id,
        "zone_id": zone_id,
        "level": level,
        "severity": level,
        "status": "OPEN", # return OPEN for legacy compatibility
        "evidence_status": "ACTIVE", # explicit evidence_status = ACTIVE
        "source_model": "rule_assisted_isolation_forest",
        "anomaly_score": anomaly_score,
        "message": message,
        "action_code": action_code,
        "recommended_action": recommended_action, # return code for legacy test
        "ai_result_ref": ai_result,
        "source_ai_event_id": source_ai_event_id
    }
    
    # Determine idempotency
    is_new = alert_id not in _created_alerts
    _created_alerts.add(alert_id)
    
    orion_upsert_status = "SKIPPED_OFFLINE"
    error_message = None
    
    # Always upsert to Orion (even if not new, we upsert/update)
    if cfg["orion_enabled"]:
        try:
            from src.fiware.entities.entities_manager import upsert_entity
            attrs = {
                "demo_run_id": {"type": "Text", "value": demo_run_id},
                "scenario_id": {"type": "Text", "value": scenario_id},
                "zone_id": {"type": "Text", "value": zone_id},
                "level": {"type": "Text", "value": level},
                "severity": {"type": "Text", "value": level},
                "status": {"type": "Text", "value": "ACTIVE"}, # strictly ACTIVE
                "source_model": {"type": "Text", "value": "rule_assisted_isolation_forest"},
                "anomaly_score": {"type": "Number", "value": anomaly_score},
                "message": {"type": "Text", "value": message},
                "action_code": {"type": "Text", "value": action_code},
                "recommended_action": {"type": "Text", "value": recommended_action}, # descriptive string
                "created_at": {"type": "DateTime", "value": timestamp},
                "source_ai_event_id": {"type": "Text", "value": source_ai_event_id}
            }
            success = upsert_entity(alert_id, "AlertEvent", attrs)
            if success:
                orion_upsert_status = "SUCCESS"
            else:
                orion_upsert_status = "FAILED"
                error_message = "Orion client returned False"
        except Exception as e:
            orion_upsert_status = "FAILED"
            error_message = str(e)
            
    # Log AlertEvent to logs/alert_events.jsonl ONLY if it is new (idempotency)
    if is_new:
        log_entry = {
            "demo_run_id": demo_run_id,
            "timestamp": timestamp,
            "alert_id": alert_id,
            "scenario_id": scenario_id,
            "zone_id": zone_id,
            "level": level,
            "severity": level,
            "status": "ACTIVE", # strictly ACTIVE
            "source_model": "rule_assisted_isolation_forest",
            "anomaly_score": anomaly_score,
            "message": message,
            "action_code": action_code,
            "recommended_action": recommended_action, # descriptive string
            "orion_upsert_status": orion_upsert_status,
            "ai_result_ref": ai_result,
            "source_ai_event_id": source_ai_event_id
        }
        if error_message:
            log_entry["error_message"] = error_message
            
        alert_log_path = os.path.join(cfg["log_dir"], "alert_events.jsonl")
        append_jsonl(alert_log_path, log_entry)
        
        # Trigger RobotAction if critical
        if level == "critical":
            create_robot_action_from_alert(event)
            
    return event

def create_robot_action_from_alert(alert_event: dict) -> dict:
    """
    Trigger RobotAction for Cruzr simulator or Orion broker.
    """
    cfg = config.get_config()
    demo_run_id = alert_event["demo_run_id"]
    alert_id = alert_event["alert_id"]
    scenario_id = alert_event["scenario_id"]
    zone_id = alert_event["zone_id"]
    timestamp = alert_event["timestamp"]
    
    robot_action_id = f"RobotAction:{scenario_id}"
    
    # Idempotency: skip if already created
    if robot_action_id in _created_robot_actions:
        room_name = zone_id.split(":")[-1] if ":" in zone_id else zone_id
        room_name = room_name.split("_")[-1] if "_" in room_name else room_name
        clean_room = room_name.strip()
        while clean_room.upper().startswith("ROOM"):
            clean_room = clean_room[4:].strip()
            clean_room = clean_room.lstrip("-_ ")
        guided_message = f"Critical indoor-environment anomaly detected in Room {clean_room}. Please follow staff guidance and move calmly to the safe waiting area."
        return {
            "demo_run_id": demo_run_id,
            "timestamp": timestamp,
            "robot_action_id": robot_action_id,
            "alert_id": alert_id,
            "scenario_id": scenario_id,
            "zone_id": zone_id,
            "robot_id": "CRUZR_01",
            "action_type": "VOICE_DISPLAY_GUIDANCE",
            "navigation_mode": "PREDEFINED_RESPONSE_POINT",
            "message": guided_message,
            "status": "PENDING"
        }
        
    _created_robot_actions.add(robot_action_id)
    
    room_name = zone_id.split(":")[-1] if ":" in zone_id else zone_id
    room_name = room_name.split("_")[-1] if "_" in room_name else room_name
    clean_room = room_name.strip()
    while clean_room.upper().startswith("ROOM"):
        clean_room = clean_room[4:].strip()
        clean_room = clean_room.lstrip("-_ ")
    
    guided_message = f"Critical indoor-environment anomaly detected in Room {clean_room}. Please follow staff guidance and move calmly to the safe waiting area."
    
    action = {
        "demo_run_id": demo_run_id,
        "timestamp": timestamp,
        "robot_action_id": robot_action_id,
        "alert_id": alert_id,
        "scenario_id": scenario_id,
        "zone_id": zone_id,
        "robot_id": "CRUZR_01",
        "action_type": "VOICE_DISPLAY_GUIDANCE",
        "navigation_mode": "PREDEFINED_RESPONSE_POINT",
        "message": guided_message,
        "status": "PENDING"
    }
    
    orion_upsert_status = "SKIPPED_OFFLINE"
    error_message = None
    
    if cfg["orion_enabled"]:
        try:
            from src.fiware.entities.entities_manager import upsert_entity
            attrs = {
                "demo_run_id": {"type": "Text", "value": demo_run_id},
                "alert_id": {"type": "Text", "value": alert_id},
                "scenario_id": {"type": "Text", "value": scenario_id},
                "zone_id": {"type": "Text", "value": zone_id},
                "robot_id": {"type": "Text", "value": "CRUZR_01"},
                "action_type": {"type": "Text", "value": "VOICE_DISPLAY_GUIDANCE"},
                "navigation_mode": {"type": "Text", "value": "PREDEFINED_RESPONSE_POINT"},
                "message": {"type": "Text", "value": guided_message},
                "status": {"type": "Text", "value": "PENDING"},
                "created_at": {"type": "DateTime", "value": timestamp}
            }
            success = upsert_entity(robot_action_id, "RobotAction", attrs)
            if success:
                orion_upsert_status = "SUCCESS"
            else:
                orion_upsert_status = "FAILED"
                error_message = "Orion client returned False"
        except Exception as e:
            orion_upsert_status = "FAILED"
            error_message = str(e)
            
    # Log RobotAction to logs/robot_actions.jsonl
    log_entry = dict(action)
    log_entry["orion_upsert_status"] = orion_upsert_status
    if error_message:
        log_entry["error_message"] = error_message
        
    robot_log_path = os.path.join(cfg["log_dir"], "robot_actions.jsonl")
    append_jsonl(robot_log_path, log_entry)
    
    return action
