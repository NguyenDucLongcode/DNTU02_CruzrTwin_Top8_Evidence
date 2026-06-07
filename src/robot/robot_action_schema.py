from src.common.time_utils import now_iso

def build_robot_action_id(demo_run_id: str, scenario_id: str, robot_id: str) -> str:
    """Builds a unique robot action ID: RobotAction:{demo_run_id}:{scenario_id}:{robot_id}"""
    return f"RobotAction:{demo_run_id}:{scenario_id}:{robot_id}"

def build_robot_action_entity(
    demo_run_id: str,
    scenario_id: str,
    scenario_source: str,
    robot_id: str,
    alert_id: str,
    zone_id: str,
    action_type: str,
    navigation_mode: str,
    target_location: str,
    message_en: str,
    message_vi: str,
    adapter: str,
    status: str = "PENDING"
) -> dict:
    """
    Builds a flat RobotAction dictionary.
    """
    timestamp = now_iso()
    action_id = build_robot_action_id(demo_run_id, scenario_id, robot_id)
    return {
        "id": action_id,
        "type": "RobotAction",
        "demo_run_id": demo_run_id,
        "scenario_id": scenario_id,
        "scenario_source": scenario_source,
        "robot_id": robot_id,
        "alert_id": alert_id,
        "zone_id": zone_id,
        "action_type": action_type,
        "navigation_mode": navigation_mode,
        "target_location": target_location,
        "message_en": message_en,
        "message_vi": message_vi,
        "status": status,
        "adapter": adapter,
        "created_at": timestamp,
        "updated_at": timestamp
    }

def to_ngsi_v2_robot_action_entity(action: dict) -> dict:
    """
    Converts a flat RobotAction dict into Orion NGSI-v2 typed representation.
    """
    return {
        "id": action["id"],
        "type": "RobotAction",
        "demo_run_id": {"type": "Text", "value": action["demo_run_id"]},
        "scenario_id": {"type": "Text", "value": action["scenario_id"]},
        "scenario_source": {"type": "Text", "value": action["scenario_source"]},
        "robot_id": {"type": "Text", "value": action["robot_id"]},
        "alert_id": {"type": "Text", "value": action["alert_id"]},
        "zone_id": {"type": "Text", "value": action["zone_id"]},
        "action_type": {"type": "Text", "value": action["action_type"]},
        "navigation_mode": {"type": "Text", "value": action["navigation_mode"]},
        "target_location": {"type": "Text", "value": action["target_location"]},
        "message_en": {"type": "Text", "value": action["message_en"]},
        "message_vi": {"type": "Text", "value": action["message_vi"]},
        "status": {"type": "Text", "value": action["status"]},
        "adapter": {"type": "Text", "value": action["adapter"]},
        "created_at": {"type": "DateTime", "value": action["created_at"]},
        "updated_at": {"type": "DateTime", "value": action["updated_at"]}
    }
