"""
Quản lý entities trong Orion
"""

import os
from datetime import datetime, timezone
from ..client import create_entity, update_entity_attrs, get_entity
from src.iot.devices import BUILDING_ID

DEMO_RUN_ID = os.getenv("DEMO_RUN_ID", "DNTU02_TOP8_RUN_2026_001")
ZONE_ID = os.getenv("ZONE_ID", "DNTU_ROOM_A101")


def upsert_entity(entity_id: str, entity_type: str, attributes: dict) -> bool:
    """Tạo mới hoặc cập nhật entity"""
    entity = {
        "id": entity_id,
        "type": entity_type,
        **attributes
    }
    
    if create_entity(entity):
        return True
    
    # Nếu entity đã tồn tại, cập nhật attributes
    return update_entity_attrs(entity_id, attributes)


def create_room(room_config: dict, extra_attributes: dict | None = None) -> bool:
    """Tạo Room entity từ config với đầy đủ attributes"""
    attributes = {}
    
    # Duyệt qua tất cả attributes trong config
    for attr in room_config["attributes"]:
        attributes[attr["name"]] = {"type": attr["type"], "value": None}
    
    # Thêm các giá trị mặc định
    attributes["demo_run_id"] = {"type": "Text", "value": DEMO_RUN_ID}
    attributes["zone_id"] = {"type": "Text", "value": ZONE_ID}
    attributes["building_id"] = {"type": "Text", "value": BUILDING_ID}
    attributes["timestamp"] = {"type": "DateTime", "value": None}
    attributes["last_updated"] = {"type": "DateTime", "value": None}

    if extra_attributes:
        attributes.update(extra_attributes)
    
    return upsert_entity(room_config["id"], room_config["type"], attributes)


def update_room_sensors(sensor_data: dict, zone_id: str = None) -> bool:
    """Cập nhật giá trị cảm biến cho Room"""
    entity_id = f"Room:{zone_id or ZONE_ID}"
    
    attrs = {}
    for key, value in sensor_data.items():
        attrs[key] = {"type": "Number", "value": value}
    
    attrs["last_updated"] = {
        "type": "DateTime",
        "value": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }
    
    return update_entity_attrs(entity_id, attrs)

def update_room_scenario(
    scenario_id: str,
    zone_id: str = None
) -> bool:

    room_id = f"Room:{zone_id or ZONE_ID}"

    attrs = {
        "scenario_id": {
            "value": scenario_id
        }
    }

    return update_entity_attrs(room_id, attrs)

def update_room_devices(device_ids: list) -> bool:
    """
    Cập nhật danh sách thiết bị cho Room
    
    Args:
        device_ids: List các device ID (ví dụ: ["Device:TEMP_A101", "Device:ENERGY_E101"])
    
    Returns:
        bool: True nếu cập nhật thành công
    """
    entity_id = f"Room:{ZONE_ID}"
    
    attrs = {
        "device_ids": {
            "type": "Array",
            "value": device_ids
        },
        "last_updated": {
            "type": "DateTime",
            "value": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        }
    }
    
    return update_entity_attrs(entity_id, attrs)

def create_alert_event(scenario_id: str, severity: str, source_room: str) -> bool:
    """Tạo AlertEvent entity trong Orion (do AI tạo)"""
    alert_event = {
        "id": f"AlertEvent:{scenario_id}",
        "type": "AlertEvent",
        "scenario_id": {"type": "Text", "value": scenario_id},
        "zone_id": {"type": "Text", "value": ZONE_ID},
        "alert_type": {"type": "Text", "value": severity},
        "severity": {"type": "Text", "value": "high" if severity == "critical" else "medium"},
        "status": {"type": "Text", "value": "PENDING"},
        "message": {"type": "Text", "value": None},
        "source_room": {"type": "Text", "value": source_room},
        "demo_run_id": {"type": "Text", "value": DEMO_RUN_ID},
        "timestamp": {"type": "DateTime", "value": None}
    }
    return upsert_entity(alert_event["id"], "AlertEvent", {
        k: v for k, v in alert_event.items() if k not in ["id", "type"]
    })


def create_robot_action(action_id: str, robot_id: str, target_room: str, scenario_id: str | None = None) -> bool:
    """Tạo RobotAction entity trong Orion (do Robot tạo)"""
    robot_action = {
        "id": action_id,
        "type": "RobotAction",
        "scenario_id": {"type": "Text", "value": scenario_id},
        "zone_id": {"type": "Text", "value": ZONE_ID},
        "robot_id": {"type": "Text", "value": robot_id},
        "action_type": {"type": "Text", "value": "VOICE_DISPLAY_GUIDANCE"},
        "target_room": {"type": "Text", "value": target_room},
        "priority": {"type": "Text", "value": "high"},
        "voice_message": {"type": "Text", "value": None},
        "display_message": {"type": "Text", "value": None},
        "navigation_status": {"type": "Text", "value": "PENDING"},
        "task_status": {"type": "Text", "value": "PENDING"},
        "status": {"type": "Text", "value": "PENDING"},
        "demo_run_id": {"type": "Text", "value": DEMO_RUN_ID}
    }
    return upsert_entity(robot_action["id"], "RobotAction", {
        k: v for k, v in robot_action.items() if k not in ["id", "type"]
    })

