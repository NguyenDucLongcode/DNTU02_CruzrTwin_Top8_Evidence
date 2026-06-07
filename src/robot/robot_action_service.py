import os
from src.common.config import LOG_DIR, ROBOT_ADAPTER, DEFAULT_ROBOT_ID
from src.common.errors import ValidationError, RobotActionError, OrionClientError
from src.common.time_utils import now_iso
from src.common.logging_utils import append_jsonl
from src.fiware.client import upsert_entity, get_entity, update_entity_attrs
from src.robot.robot_action_schema import (
    build_robot_action_id,
    build_robot_action_entity,
    to_ngsi_v2_robot_action_entity
)
from src.robot.robot_lifecycle import validate_robot_transition
from src.robot.adapters import MockCruzrAdapter, LocalBridgeAdapter, RealCruzrAdapter

ROBOT_LOG_PATH = os.path.join(LOG_DIR, "robot_action.jsonl")

# Standard bilingual messages
MSG_EN = "Critical indoor-environment anomaly detected in Room A101. Please follow staff guidance and move calmly to the safe waiting area."
MSG_VI = "Phát hiện bất thường nghiêm trọng trong phòng A101. Vui lòng bình tĩnh làm theo hướng dẫn của nhân viên và di chuyển đến khu vực an toàn."

def get_adapter():
    """Gets configured robot adapter instance."""
    adapter_name = ROBOT_ADAPTER.lower()
    if adapter_name == "mock":
        return MockCruzrAdapter()
    elif adapter_name == "local_bridge":
        return LocalBridgeAdapter()
    elif adapter_name == "real":
        return RealCruzrAdapter()
    else:
        # Default fallback
        return MockCruzrAdapter()

def append_robot_log(action: dict, event_type: str, orion_status: str, dispatch_res: dict | None = None, error: str | None = None):
    log_entry = {
        "demo_run_id": action["demo_run_id"],
        "timestamp": now_iso(),
        "scenario_id": action["scenario_id"],
        "scenario_source": action["scenario_source"],
        "zone_id": action["zone_id"],
        "event_type": event_type,
        "robot_action_id": action["id"],
        "robot_id": action["robot_id"],
        "alert_id": action["alert_id"],
        "action_type": action["action_type"],
        "navigation_mode": action["navigation_mode"],
        "target_location": action["target_location"],
        "message_en": action["message_en"],
        "message_vi": action["message_vi"],
        "adapter": action["adapter"],
        "status": action["status"],
        "dispatch_result": dispatch_res,
        "orion_upsert_status": orion_status,
        "error": error
    }
    append_jsonl(ROBOT_LOG_PATH, log_entry)

def create_robot_action(alert_event: dict) -> dict:
    """
    Creates a RobotAction in Orion and logs the creation.
    Returns:
        dict: The created RobotAction dictionary, or warning response.
    """
    if alert_event.get("level") != "critical":
        return {
            "status": "NO_ROBOT_ACTION_REQUIRED",
            "reason": "Warning alert only requires dashboard notification."
        }
        
    demo_run_id = alert_event["demo_run_id"]
    scenario_id = alert_event["scenario_id"]
    scenario_source = alert_event["scenario_source"]
    alert_id = alert_event["id"]
    zone_id = alert_event["zone_id"]
    
    # Predefined location
    target_location = "RESPONSE_POINT_A101"
    
    adapter_instance = get_adapter()
    adapter_name = adapter_instance.__class__.__name__
    
    action = build_robot_action_entity(
        demo_run_id=demo_run_id,
        scenario_id=scenario_id,
        scenario_source=scenario_source,
        robot_id=DEFAULT_ROBOT_ID,
        alert_id=alert_id,
        zone_id=zone_id,
        action_type="VOICE_DISPLAY_GUIDANCE",
        navigation_mode="PREDEFINED_RESPONSE_POINT",
        target_location=target_location,
        message_en=MSG_EN,
        message_vi=MSG_VI,
        adapter=adapter_name,
        status="PENDING"
    )
    
    # Upsert to Orion Context Broker
    ngsi_entity = to_ngsi_v2_robot_action_entity(action)
    orion_status = "success"
    error_msg = None
    try:
        res = upsert_entity(ngsi_entity)
        if not res["success"]:
            orion_status = "failed"
            error_msg = res["error"]
    except Exception as e:
        orion_status = "failed"
        error_msg = str(e)
        
    append_robot_log(action, "ROBOT_ACTION_CREATED", orion_status, error=error_msg)
    return action

def dispatch_robot_action(robot_action: dict) -> dict:
    """
    Dispatches the RobotAction using the configured adapter.
    Updates the RobotAction and AlertEvent status accordingly in Orion.
    """
    adapter_instance = get_adapter()
    
    # 1. Update status to SENT_TO_BRIDGE
    robot_action = update_robot_action_status(robot_action["id"], "SENT_TO_BRIDGE")
    
    # 2. Dispatch
    try:
        dispatch_res = adapter_instance.dispatch(robot_action)
        status = dispatch_res.get("status", "ERROR")
    except Exception as e:
        dispatch_res = {"status": "ERROR", "error": str(e)}
        status = "ERROR"
        
    # 3. Update status based on dispatch outcome
    if status == "GUIDANCE_DELIVERED":
        # First transition: SENT_TO_BRIDGE -> IN_PROGRESS
        robot_action = update_robot_action_status(robot_action["id"], "IN_PROGRESS")
        # Second transition: IN_PROGRESS -> GUIDANCE_DELIVERED
        robot_action = update_robot_action_status(robot_action["id"], "GUIDANCE_DELIVERED")
        
        # Log dispatched event
        append_robot_log(robot_action, "ROBOT_ACTION_DISPATCHED", "success", dispatch_res)
    else:
        # Fail transition
        robot_action = update_robot_action_status(robot_action["id"], "ERROR")
        append_robot_log(robot_action, "ROBOT_ACTION_ERROR", "success", dispatch_res, error=dispatch_res.get("error"))
        
    return robot_action

def update_robot_action_status(robot_action_id: str, status: str, note: str | None = None) -> dict:
    """
    Updates the status of an existing RobotAction, performing lifecycle checks.
    """
    raw_action = get_entity(robot_action_id)
    if not raw_action:
        raise RobotActionError(f"RobotAction {robot_action_id} not found.")
        
    current_status = raw_action.get("status", {}).get("value", "PENDING")
    
    # Perform lifecycle check
    validate_robot_transition(current_status, status)
    
    updated_at = now_iso()
    ngsi_attrs = {
        "status": {"type": "Text", "value": status},
        "updated_at": {"type": "DateTime", "value": updated_at}
    }
    
    orion_status = "success"
    error_msg = None
    try:
        res = update_entity_attrs(robot_action_id, ngsi_attrs)
        if not res["success"]:
            orion_status = "failed"
            error_msg = res["error"]
    except Exception as e:
        orion_status = "failed"
        error_msg = str(e)
        
    action = {
        "id": robot_action_id,
        "type": "RobotAction",
        "demo_run_id": raw_action.get("demo_run_id", {}).get("value", "unknown"),
        "scenario_id": raw_action.get("scenario_id", {}).get("value", "unknown"),
        "scenario_source": raw_action.get("scenario_source", {}).get("value", "active_state_fallback"),
        "robot_id": raw_action.get("robot_id", {}).get("value", DEFAULT_ROBOT_ID),
        "alert_id": raw_action.get("alert_id", {}).get("value", "unknown"),
        "zone_id": raw_action.get("zone_id", {}).get("value", "unknown"),
        "action_type": raw_action.get("action_type", {}).get("value", "unknown"),
        "navigation_mode": raw_action.get("navigation_mode", {}).get("value", "unknown"),
        "target_location": raw_action.get("target_location", {}).get("value", "unknown"),
        "message_en": raw_action.get("message_en", {}).get("value", ""),
        "message_vi": raw_action.get("message_vi", {}).get("value", ""),
        "status": status,
        "adapter": raw_action.get("adapter", {}).get("value", "MockCruzrAdapter"),
        "created_at": raw_action.get("created_at", {}).get("value", updated_at),
        "updated_at": updated_at
    }
    
    append_robot_log(action, "ROBOT_ACTION_STATUS_CHANGED", orion_status)
    return action
