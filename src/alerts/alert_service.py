import os
from src.common.config import LOG_DIR
from src.common.errors import ValidationError, AlertServiceError, OrionClientError
from src.common.time_utils import now_iso
from src.common.logging_utils import append_jsonl, build_base_log_context
from src.fiware.client import upsert_entity, get_entity, update_entity_attrs
from src.alerts.alert_schema import (
    build_alert_event_id,
    build_alert_event_entity,
    to_ngsi_v2_alert_entity
)
from src.alerts.alert_lifecycle import validate_alert_transition

ALERT_LOG_PATH = os.path.join(LOG_DIR, "alert_events.jsonl")

def build_alert_id(demo_run_id: str, scenario_id: str) -> str:
    return build_alert_event_id(demo_run_id, scenario_id)

def append_alert_log(alert: dict, event_type: str, orion_status: str, error: str | None = None):
    """
    Appends a log record to logs/alert_events.jsonl.
    """
    log_entry = {
        "demo_run_id": alert["demo_run_id"],
        "timestamp": now_iso(),
        "scenario_id": alert["scenario_id"],
        "scenario_source": alert["scenario_source"],
        "zone_id": alert["zone_id"],
        "event_type": event_type,
        "alert_id": alert["id"],
        "source_entity_id": alert["source_entity_id"],
        "level": alert["level"],
        "status": alert["status"],
        "cause": alert["cause"],
        "ai_detection_ref": alert["ai_result"],
        "recommended_action": alert["recommended_action"],
        "orion_upsert_status": orion_status,
        "error": error
    }
    append_jsonl(ALERT_LOG_PATH, log_entry)

def create_alert_event(ai_result: dict, room_state: dict) -> dict:
    """
    Creates an AlertEvent based on AI result.
    If normal -> returns no alert dict.
    If warning/critical -> validates idempotency and upserts to Orion.
    """
    predicted_level = ai_result["predicted_level"]
    if predicted_level == "normal":
        return {
            "status": "NO_ALERT",
            "reason": "Predicted level is normal."
        }
        
    demo_run_id = ai_result["demo_run_id"]
    scenario_id = ai_result["scenario_id"]
    scenario_source = ai_result["scenario_source"]
    zone_id = ai_result["zone_id"]
    source_entity_id = ai_result["source_entity_id"]
    recommended_action = ai_result["recommended_action"]
    
    # recommended action adjustments for alert levels
    if predicted_level == "warning":
        rec_act = "SHOW_DASHBOARD_WARNING"
    else:
        rec_act = "DISPATCH_CRUZR_GUIDANCE"
        
    # Cause values
    cause = {
        "temperature": ai_result["features"]["temperature"],
        "humidity": ai_result["features"]["humidity"],
        "air_quality_or_co2": ai_result["features"]["air_quality_or_co2"],
        "smoke_status": ai_result["features"]["smoke_status"],
        "energy_consumption": ai_result["features"]["energy_consumption"]
    }
    
    alert_id = build_alert_id(demo_run_id, scenario_id)
    
    # Idempotency check: see if it exists
    existing_alert = None
    orion_status = "skipped"
    error_msg = None
    
    try:
        existing_alert = get_entity(alert_id)
        if existing_alert:
            orion_status = "success"
    except OrionClientError as e:
        error_msg = f"Orion query failed: {e}"
        orion_status = "failed"
        
    if existing_alert:
        # Update existing alert
        updated_at = now_iso()
        
        # Flatten Orion's NGSI response to dict for updating
        alert = {
            "id": alert_id,
            "type": "AlertEvent",
            "demo_run_id": demo_run_id,
            "scenario_id": scenario_id,
            "scenario_source": scenario_source,
            "zone_id": zone_id,
            "source_entity_id": source_entity_id,
            "level": predicted_level,
            "status": existing_alert.get("status", {}).get("value", "OPEN"),
            "cause": cause,
            "ai_result": {
                "model": ai_result["model"],
                "anomaly_score": ai_result["anomaly_score"],
                "predicted_level": predicted_level,
                "rationale": ai_result["rationale"]
            },
            "recommended_action": rec_act,
            "created_at": existing_alert.get("created_at", {}).get("value", updated_at),
            "updated_at": updated_at
        }
        
        # Convert to NGSI for patching
        ngsi_attrs = {
            "updated_at": {"type": "DateTime", "value": updated_at},
            "cause": {"type": "StructuredValue", "value": cause},
            "ai_result": {"type": "StructuredValue", "value": alert["ai_result"]},
            "level": {"type": "Text", "value": alert["level"]},
            "recommended_action": {"type": "Text", "value": rec_act}
        }
        
        try:
            res = update_entity_attrs(alert_id, ngsi_attrs)
            if res["success"]:
                orion_status = "success"
            else:
                orion_status = "failed"
                error_msg = res["error"]
        except Exception as e:
            orion_status = "failed"
            error_msg = str(e)
            
        append_alert_log(alert, "ALERT_UPDATED", orion_status, error_msg)
        return alert
    else:
        # Create a new alert
        alert = build_alert_event_entity(
            demo_run_id=demo_run_id,
            scenario_id=scenario_id,
            scenario_source=scenario_source,
            zone_id=zone_id,
            source_entity_id=source_entity_id,
            level=predicted_level,
            cause=cause,
            ai_result=ai_result,
            recommended_action=rec_act,
            status="OPEN"
        )
        
        ngsi_entity = to_ngsi_v2_alert_entity(alert)
        try:
            res = upsert_entity(ngsi_entity)
            if res["success"]:
                orion_status = "success"
            else:
                orion_status = "failed"
                error_msg = res["error"]
        except Exception as e:
            orion_status = "failed"
            error_msg = str(e)
            
        append_alert_log(alert, "ALERT_CREATED", orion_status, error_msg)
        return alert

def update_alert_status(alert_id: str, status: str, note: str | None = None) -> dict:
    """
    Updates the status of an existing alert.
    Performs transition validation.
    """
    existing_alert = None
    try:
        existing_alert = get_entity(alert_id)
    except OrionClientError as e:
        raise AlertServiceError(f"Could not retrieve alert: {e}")
        
    if not existing_alert:
        raise AlertServiceError(f"Alert {alert_id} not found in Orion.")
        
    current_status = existing_alert.get("status", {}).get("value", "OPEN")
    
    # Perform validation
    validate_alert_transition(current_status, status, note)
    
    # Update attributes in Orion
    updated_at = now_iso()
    ngsi_attrs = {
        "status": {"type": "Text", "value": status},
        "updated_at": {"type": "DateTime", "value": updated_at}
    }
    
    orion_status = "success"
    error_msg = None
    try:
        res = update_entity_attrs(alert_id, ngsi_attrs)
        if not res["success"]:
            orion_status = "failed"
            error_msg = res["error"]
    except Exception as e:
        orion_status = "failed"
        error_msg = str(e)
        
    # Rebuild flat alert dict for logging
    alert = {
        "id": alert_id,
        "type": "AlertEvent",
        "demo_run_id": existing_alert.get("demo_run_id", {}).get("value", "unknown"),
        "scenario_id": existing_alert.get("scenario_id", {}).get("value", "unknown"),
        "scenario_source": existing_alert.get("scenario_source", {}).get("value", "active_state_fallback"),
        "zone_id": existing_alert.get("zone_id", {}).get("value", "unknown"),
        "source_entity_id": existing_alert.get("source_entity_id", {}).get("value", "unknown"),
        "level": existing_alert.get("level", {}).get("value", "warning"),
        "status": status,
        "cause": existing_alert.get("cause", {}).get("value", {}),
        "ai_result": existing_alert.get("ai_result", {}).get("value", {}),
        "recommended_action": existing_alert.get("recommended_action", {}).get("value", ""),
        "created_at": existing_alert.get("created_at", {}).get("value", updated_at),
        "updated_at": updated_at
    }
    
    append_alert_log(alert, "ALERT_STATUS_CHANGED", orion_status, error_msg)
    return alert

def get_alert_event(alert_id: str) -> dict:
    """Gets alert event, returning flat representation."""
    raw = get_entity(alert_id)
    if not raw:
        return {}
    # Flatten it
    return {
        "id": raw["id"],
        "type": raw["type"],
        "demo_run_id": raw.get("demo_run_id", {}).get("value"),
        "scenario_id": raw.get("scenario_id", {}).get("value"),
        "scenario_source": raw.get("scenario_source", {}).get("value"),
        "zone_id": raw.get("zone_id", {}).get("value"),
        "source_entity_id": raw.get("source_entity_id", {}).get("value"),
        "level": raw.get("level", {}).get("value"),
        "status": raw.get("status", {}).get("value"),
        "cause": raw.get("cause", {}).get("value"),
        "ai_result": raw.get("ai_result", {}).get("value"),
        "recommended_action": raw.get("recommended_action", {}).get("value"),
        "created_at": raw.get("created_at", {}).get("value"),
        "updated_at": raw.get("updated_at", {}).get("value")
    }
