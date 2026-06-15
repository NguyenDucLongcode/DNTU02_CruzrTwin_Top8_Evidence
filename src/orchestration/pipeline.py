import os
from datetime import datetime, timezone
from src.ai.detector import detect_anomaly
from src.alerts.alert_service import create_alert_event
from src.common import config
from src.common.logging_utils import append_jsonl
import pandas as pd

def parse_payload(payload: dict) -> dict:
    # 1. Webhook payload
    if "data" in payload and isinstance(payload["data"], list) and payload["data"]:
        entity = payload["data"][0]
        return parse_entity(entity)
    # 2. Orion entity
    elif "id" in payload and "type" in payload:
        return parse_entity(payload)
    # 3. Simple dictionary
    return payload

def parse_entity(entity: dict) -> dict:
    def get_val(field):
        attr = entity.get(field)
        if isinstance(attr, dict) and "value" in attr:
            return attr["value"]
        return attr
    
    parsed = {}
    for key in entity:
        if key not in ["id", "type"]:
            parsed[key] = get_val(key)
    if "id" in entity:
        parsed["id"] = entity["id"]
    if "type" in entity:
        parsed["type"] = entity["type"]
    return parsed

def process_ai_detector_event(orion_payload: dict, scenario_id: str = None,) -> dict:
    """
    Orchestrate the processing of a single sensor reading event.
    Returns a dictionary containing:
    - processing_status: SUCCESS or SKIPPED_INCOMPLETE_SENSOR_DATA
    - ai_result: result from the AI detector
    - alert_event: created AlertEvent dictionary (or None if normal)
    """
    cfg = config.get_config()
    
    # 1. Parse payload
    parsed_data = parse_payload(orion_payload)
    
    # 2. Identify identifiers
    demo_run_id = parsed_data.get("demo_run_id") or cfg["demo_run_id"]
    
    # scenario_id fallback
    if scenario_id is None:
        scenario_id = parsed_data.get("scenario_id") or parsed_data.get("scenario") or cfg["default_scenario_id"]
            
    zone_id = parsed_data.get("zone_id") or cfg["default_zone_id"]
    
    # 3. Extract sensor fields with fallbacks
    temp = parsed_data.get("temperature")
    hum = parsed_data.get("humidity")
    co2 = parsed_data.get("air_quality_or_co2") if parsed_data.get("air_quality_or_co2") is not None else parsed_data.get("co2")
    smoke = parsed_data.get("smoke_status") if parsed_data.get("smoke_status") is not None else parsed_data.get("smoke")
    power = parsed_data.get("energy_consumption") if parsed_data.get("energy_consumption") is not None else parsed_data.get("power")
    
    # 4. If Orion is enabled and some fields are missing, query Room state from Orion
    if cfg["orion_enabled"] and (temp is None or hum is None or co2 is None or smoke is None or power is None):
        try:
            from src.fiware.entities.query import get_room_state
            room = get_room_state(zone_id)
            if room:
                room_data = parse_entity(room)
                if temp is None: temp = room_data.get("temperature")
                if hum is None: hum = room_data.get("humidity")
                if co2 is None: co2 = room_data.get("air_quality_or_co2") if room_data.get("air_quality_or_co2") is not None else room_data.get("co2")
                if smoke is None: smoke = room_data.get("smoke_status") if room_data.get("smoke_status") is not None else room_data.get("smoke")
                if power is None: power = room_data.get("energy_consumption") if room_data.get("energy_consumption") is not None else room_data.get("power")
        except Exception as e:
            print(f"Error querying Room state from Orion: {e}")
            
    # 5. Check if we still have incomplete sensor data
    if temp is None or hum is None or co2 is None or smoke is None or power is None:
        missing_fields = []
        if temp is None: missing_fields.append("temperature")
        if hum is None: missing_fields.append("humidity")
        if co2 is None: missing_fields.append("air_quality_or_co2")
        if smoke is None: missing_fields.append("smoke_status")
        if power is None: missing_fields.append("energy_consumption")
        return {
            "processing_status": "SKIPPED_INCOMPLETE_SENSOR_DATA",
            "ai_result": None,
            "alert_event": None,
            "missing_fields": missing_fields
        }
    
    # Mapping for AI feature vector
    sensor_features = {
        "temperature": float(temp),
        "humidity": float(hum),
        "smoke": float(smoke),
        "co2": float(co2),
        "power": float(power)
    }
    
    # 6. Run Isolation Forest + Rule engine
    ai_result = detect_anomaly(sensor_features)
    lvl = ai_result["predicted_level"]
    
    # Determine expected_label
    expected_label = parsed_data.get("expected_label") or parsed_data.get("expected")
    if not expected_label and scenario_id:
        if "CRITICAL" in scenario_id:
            expected_label = "critical"
        elif "WARNING" in scenario_id:
            expected_label = "warning"
        elif "NORMAL" in scenario_id:
            expected_label = "normal"
        else:
            expected_label = None
    
    # Load profile to check critical combinations dynamically
    from src.ai.detector import load_sensor_profile
    from src.ai.rule_engine import DEFAULT_BASELINE
    profile_path = cfg.get("sensor_profile_path", "models/sensor_profile.json")
    profile = load_sensor_profile(profile_path)
    baseline = None
    if profile is not None:
        hour_str = None
        ts = ai_result.get("timestamp")
        if ts:
            try:
                dt = pd.to_datetime(ts.replace("Z", "+00:00") if isinstance(ts, str) else ts)
                hour_str = str(dt.hour)
            except Exception:
                pass
        if hour_str is not None and "hourly_baseline" in profile and hour_str in profile["hourly_baseline"]:
            baseline = profile["hourly_baseline"][hour_str]
        if baseline is None and "global_statistics" in profile:
            baseline = profile["global_statistics"]
    if baseline is None:
        baseline = DEFAULT_BASELINE

    b_temp = baseline.get("temperature", DEFAULT_BASELINE["temperature"])
    b_co2 = baseline.get("co2", DEFAULT_BASELINE["co2"])

    # 7. Action code and recommended action separation
    if lvl == "normal":
        action_code = "NO_ACTION"
        rec_action = "No action required. Continue monitoring."
    elif lvl == "warning":
        action_code = "CHECK_ROOM"
        rec_action = "Create warning AlertEvent and notify operator."
    elif lvl == "critical":
        action_code = "DISPATCH_CRUZR_GUIDANCE"
        if float(temp) >= b_temp["critical_high"] and float(smoke) >= 1.0 and float(co2) >= b_co2["critical_high"]:
            rec_action = "Create critical AlertEvent, send Cruzr to response point, and request operator acknowledgement. Safety-critical actuation should remain operator-approved or simulated."
        else:
            rec_action = "Send Cruzr to response point and request operator acknowledgement."
            
    ai_result["recommended_action"] = rec_action
    
    # source_ai_event_id construction
    source_ai_event_id = f"AIEvent:{scenario_id}"
    
    # 8. Write AI Detection Log to logs/ai_detection.jsonl
    ts = ai_result.get("timestamp") or datetime.now(timezone.utc).isoformat()
    ai_log_entry = {
        "demo_run_id": demo_run_id,
        "timestamp": ts,
        "scenario_id": scenario_id,
        "zone_id": zone_id,
        "source": "FIWARE_ORION",
        "model": "rule_assisted_isolation_forest",
        "sensor_values": {
            "temperature": float(temp),
            "humidity": float(hum),
            "air_quality_or_co2": float(co2),
            "smoke_status": 1 if float(smoke) >= 1.0 else 0,
            "energy_consumption": float(power),
            "raw_smoke_value": float(smoke)
        },
        "anomaly_score": float(ai_result.get("anomaly_score", 0.0)),
        "predicted_level": lvl,
        "expected_label": expected_label,
        "rationale": ai_result.get("rationale"),
        "action_code": action_code,
        "recommended_action": rec_action,
        "source_ai_event_id": source_ai_event_id
    }
    
    ai_log_path = os.path.join(cfg["log_dir"], "ai_detection.jsonl")
    append_jsonl(ai_log_path, ai_log_entry)
    
    alert_event = None
    if lvl in ["warning", "critical"]:
        # Pass necessary attributes for create_alert_event
        ai_result["demo_run_id"] = demo_run_id
        ai_result["scenario_id"] = scenario_id
        ai_result["zone_id"] = zone_id
        ai_result["action_code"] = action_code
        ai_result["recommended_action"] = rec_action
        ai_result["source_ai_event_id"] = source_ai_event_id
        
        alert_event = create_alert_event(
            ai_result, 
            demo_run_id=demo_run_id, 
            scenario_id=scenario_id, 
            zone_id=zone_id
        )
        

    
    return {
        "processing_status": "SUCCESS",
        "ai_result": ai_result,
        "alert_event": alert_event
    }
