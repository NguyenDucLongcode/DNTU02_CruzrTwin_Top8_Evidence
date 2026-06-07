import os
import json
from src.common.config import LOG_DIR, DEMO_RUN_ID, DEFAULT_ZONE_ID
from src.common.time_utils import now_iso
from src.common.logging_utils import append_jsonl
from src.common.errors import ValidationError, DetectionError, AlertServiceError, RobotActionError
from src.fiware.client import get_entity
from src.ai.detector import detect_anomaly
from src.alerts.alert_service import create_alert_event, update_alert_status
from src.robot.robot_action_service import create_robot_action, dispatch_robot_action

AI_LOG_PATH = os.path.join(LOG_DIR, "ai_detection.jsonl")
ACTIVE_SCENARIO_PATH = os.path.join(LOG_DIR, "active_scenario.json")

def _extract_val(data: dict, key: str, default=None):
    if key not in data:
        return default
    val = data[key]
    if isinstance(val, dict) and "value" in val:
        return val["value"]
    return val

def process_room_state(room_state: dict) -> dict:
    """
    Main closed-loop orchestration pipeline.
    Room State -> AI Detection -> AlertEvent -> RobotAction -> Dispatch.
    """
    errors = []
    trace_refs = {}
    
    # 1. Resolve basic metadata
    zone_id = _extract_val(room_state, "zone_id") or DEFAULT_ZONE_ID
    source_entity_id = room_state.get("id") or f"Room:{zone_id}"
    timestamp = _extract_val(room_state, "timestamp") or _extract_val(room_state, "last_updated") or now_iso()
    
    # 2. Resolve Scenario ID and Demo Run ID following priority rules
    scenario_id = None
    scenario_source = None
    
    # Priority 1: Payload
    if "scenario_id" in room_state:
        scenario_id = _extract_val(room_state, "scenario_id")
        scenario_source = "payload"
        
    # Priority 2: Orion Room entity
    if not scenario_id:
        try:
            orion_room = get_entity(f"Room:{zone_id}")
            if orion_room and "scenario_id" in orion_room:
                scenario_id = _extract_val(orion_room, "scenario_id")
                scenario_source = "orion_entity"
        except Exception as e:
            errors.append(f"Orion room fetch failed: {e}")
            
    # Priority 3: logs/active_scenario.json fallback
    if not scenario_id:
        if os.path.exists(ACTIVE_SCENARIO_PATH):
            try:
                with open(ACTIVE_SCENARIO_PATH, "r", encoding="utf-8") as f:
                    act_data = json.load(f)
                    scenario_id = act_data.get("scenario_id")
                    scenario_source = "active_state_fallback"
            except Exception as e:
                errors.append(f"Active scenario file read error: {e}")
                
    # Priority 4: manual_demo fallback
    if not scenario_id:
        scenario_id = "SCN_NORMAL_001"
        scenario_source = "manual_demo"
        
    # Resolve demo run id
    run_id = _extract_val(room_state, "demo_run_id")
    if not run_id:
        if os.path.exists(ACTIVE_SCENARIO_PATH):
            try:
                with open(ACTIVE_SCENARIO_PATH, "r", encoding="utf-8") as f:
                    act_data = json.load(f)
                    run_id = act_data.get("demo_run_id")
            except Exception:
                pass
    if not run_id:
        run_id = DEMO_RUN_ID
        
    # Normalize features
    temp = _extract_val(room_state, "temperature", 0.0)
    hum = _extract_val(room_state, "humidity", 0.0)
    co2 = _extract_val(room_state, "air_quality_or_co2") or _extract_val(room_state, "co2", 0)
    smoke = _extract_val(room_state, "smoke_status") or _extract_val(room_state, "smoke", 0)
    energy = _extract_val(room_state, "energy_consumption") or _extract_val(room_state, "energy", 0.0)
    device_status = _extract_val(room_state, "device_status", "ON")
    expected_label = _extract_val(room_state, "expected_label")
    
    # 3. Normalize reading dictionary for AI Detector
    ai_input = {
        "demo_run_id": run_id,
        "scenario_id": scenario_id,
        "scenario_source": scenario_source,
        "zone_id": zone_id,
        "timestamp": timestamp,
        "source_entity_id": source_entity_id,
        "temperature": temp,
        "humidity": hum,
        "air_quality_or_co2": co2,
        "smoke_status": smoke,
        "energy_consumption": energy,
        "device_status": device_status,
        "expected_label": expected_label
    }
    
    # 4. Call Anomaly Detector
    ai_result = {}
    try:
        ai_result = detect_anomaly(ai_input)
        append_jsonl(AI_LOG_PATH, ai_result)
        trace_refs["ai_detection_log"] = AI_LOG_PATH
    except ValidationError as e:
        errors.append(f"AI Input Validation Error: {e}")
        return {
            "demo_run_id": run_id,
            "scenario_id": scenario_id,
            "scenario_source": scenario_source,
            "zone_id": zone_id,
            "pipeline_status": "VALIDATION_ERROR",
            "ai_result": {},
            "alert_event": {},
            "robot_action": {},
            "errors": errors,
            "trace_refs": trace_refs
        }
    except Exception as e:
        errors.append(f"AI Detection failed: {e}")
        return {
            "demo_run_id": run_id,
            "scenario_id": scenario_id,
            "scenario_source": scenario_source,
            "zone_id": zone_id,
            "pipeline_status": "DETECTION_ERROR",
            "ai_result": {},
            "alert_event": {},
            "robot_action": {},
            "errors": errors,
            "trace_refs": trace_refs
        }
        
    predicted_level = ai_result["predicted_level"]
    alert_event = {}
    robot_action = {}
    
    # 5. Normal path
    if predicted_level == "normal":
        return {
            "demo_run_id": run_id,
            "scenario_id": scenario_id,
            "scenario_source": scenario_source,
            "zone_id": zone_id,
            "pipeline_status": "NO_ACTION",
            "ai_result": ai_result,
            "alert_event": {},
            "robot_action": {},
            "errors": errors,
            "trace_refs": trace_refs
        }
        
    # 6. Warning path
    if predicted_level == "warning":
        try:
            alert_event = create_alert_event(ai_result, room_state)
            trace_refs["alert_event_id"] = alert_event["id"]
            pipeline_status = "WARNING_ALERT_CREATED"
        except Exception as e:
            errors.append(f"Alert creation failed: {e}")
            pipeline_status = "ALERT_ERROR"
            
        return {
            "demo_run_id": run_id,
            "scenario_id": scenario_id,
            "scenario_source": scenario_source,
            "zone_id": zone_id,
            "pipeline_status": pipeline_status,
            "ai_result": ai_result,
            "alert_event": alert_event,
            "robot_action": {},
            "errors": errors,
            "trace_refs": trace_refs
        }
        
    # 7. Critical path
    if predicted_level == "critical":
        try:
            # Create AlertEvent
            alert_event = create_alert_event(ai_result, room_state)
            trace_refs["alert_event_id"] = alert_event["id"]
            
            # Create RobotAction
            robot_action = create_robot_action(alert_event)
            trace_refs["robot_action_id"] = robot_action["id"]
            
            # Dispatch
            robot_action = dispatch_robot_action(robot_action)
            
            # Update AlertEvent Status
            if robot_action["status"] == "GUIDANCE_DELIVERED":
                alert_event = update_alert_status(alert_event["id"], "DISPATCHED")
                pipeline_status = "CRITICAL_ALERT_AND_ROBOT_ACTION_CREATED"
            else:
                alert_event = update_alert_status(alert_event["id"], "ERROR", note="Robot dispatch failed")
                pipeline_status = "ROBOT_DISPATCH_FAILED"
                
        except Exception as e:
            errors.append(f"Critical closed-loop orchestration failed: {e}")
            pipeline_status = "CRITICAL_ORCHESTRATION_ERROR"
            
        return {
            "demo_run_id": run_id,
            "scenario_id": scenario_id,
            "scenario_source": scenario_source,
            "zone_id": zone_id,
            "pipeline_status": pipeline_status,
            "ai_result": ai_result,
            "alert_event": alert_event,
            "robot_action": robot_action,
            "errors": errors,
            "trace_refs": trace_refs
        }
        
    return {
        "demo_run_id": run_id,
        "scenario_id": scenario_id,
        "scenario_source": scenario_source,
        "zone_id": zone_id,
        "pipeline_status": "UNKNOWN_LEVEL",
        "ai_result": ai_result,
        "alert_event": {},
        "robot_action": {},
        "errors": errors,
        "trace_refs": trace_refs
    }
