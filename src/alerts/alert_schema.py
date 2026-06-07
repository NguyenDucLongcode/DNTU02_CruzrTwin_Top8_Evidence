from src.common.time_utils import now_iso

def build_alert_event_id(demo_run_id: str, scenario_id: str) -> str:
    """Builds a unique alert ID: AlertEvent:{demo_run_id}:{scenario_id}"""
    return f"AlertEvent:{demo_run_id}:{scenario_id}"

def build_alert_event_entity(
    demo_run_id: str,
    scenario_id: str,
    scenario_source: str,
    zone_id: str,
    source_entity_id: str,
    level: str,
    cause: dict,
    ai_result: dict,
    recommended_action: str,
    status: str = "OPEN"
) -> dict:
    """
    Builds a standard flat AlertEvent dictionary.
    """
    timestamp = now_iso()
    alert_id = build_alert_event_id(demo_run_id, scenario_id)
    return {
        "id": alert_id,
        "type": "AlertEvent",
        "demo_run_id": demo_run_id,
        "scenario_id": scenario_id,
        "scenario_source": scenario_source,
        "zone_id": zone_id,
        "source_entity_id": source_entity_id,
        "level": level,
        "status": status,
        "cause": cause,
        "ai_result": {
            "model": ai_result.get("model"),
            "anomaly_score": ai_result.get("anomaly_score"),
            "predicted_level": ai_result.get("predicted_level"),
            "rationale": ai_result.get("rationale")
        },
        "recommended_action": recommended_action,
        "created_at": timestamp,
        "updated_at": timestamp
    }

def to_ngsi_v2_alert_entity(alert: dict) -> dict:
    """
    Converts a flat AlertEvent dict into an NGSI-v2 typed representation.
    """
    return {
        "id": alert["id"],
        "type": "AlertEvent",
        "demo_run_id": {"type": "Text", "value": alert["demo_run_id"]},
        "scenario_id": {"type": "Text", "value": alert["scenario_id"]},
        "scenario_source": {"type": "Text", "value": alert["scenario_source"]},
        "zone_id": {"type": "Text", "value": alert["zone_id"]},
        "source_entity_id": {"type": "Text", "value": alert["source_entity_id"]},
        "level": {"type": "Text", "value": alert["level"]},
        "status": {"type": "Text", "value": alert["status"]},
        "cause": {"type": "StructuredValue", "value": alert["cause"]},
        "ai_result": {"type": "StructuredValue", "value": alert["ai_result"]},
        "recommended_action": {"type": "Text", "value": alert["recommended_action"]},
        "created_at": {"type": "DateTime", "value": alert["created_at"]},
        "updated_at": {"type": "DateTime", "value": alert["updated_at"]}
    }
