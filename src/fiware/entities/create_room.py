"""
Bootstrap Orion demo entities for the full scenario.

Creates the shared Room/Device/AlertEvent/RobotAction state used in the
demo chain so SensorReading -> Orion Room State -> AI Detection ->
AlertEvent -> RobotAction -> OperatorAck can be traced with one demo_run_id.
"""

import os
import sys

# Thêm đường dẫn để import từ src
ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
    )
)

sys.path.insert(0, ROOT_DIR)

from src.iot.devices import ROOM_CONFIG, DEMO_RUN_ID, ZONE_ID
from src.fimat.register import register_all_devices
from src.fiware.entities.entities_manager import (
    create_room as create_room_entity,
    create_alert_event,
    create_robot_action,
)
from src.fiware.entities.query import print_summary

SCENARIO_ID = "SCN_CRITICAL_001"
ROBOT_ID = "CRUZR_01"
ALERT_ID = f"AlertEvent:{SCENARIO_ID}"
ROBOT_ACTION_ID = "RobotAction:CRUZR_ACTION_001"

def main():
    print("=" * 50)
    print("Bootstrapping Demo Entities in Orion")
    print("=" * 50)
    print(f"   demo_run_id: {DEMO_RUN_ID}")
    print(f"   scenario_id: {SCENARIO_ID}")
    print(f"   zone_id    : {ZONE_ID}")
    print("-" * 50)

    print("Registering IoT devices...")
    register_all_devices()

    print(f"Creating Room entity: {ROOM_CONFIG['id']}")
    room_extra_attrs = {
        "scenario_id": {"type": "Text", "value": SCENARIO_ID},
        "device_status": {"type": "Text", "value": "ON"},
        "anomaly_detected": {"type": "Boolean", "value": False},
        "robot_response_required": {"type": "Boolean", "value": False},
        "robot_status": {"type": "Text", "value": "idle"},
        "evacuation_status": {"type": "Text", "value": "normal"},
        "emergency_level": {"type": "Text", "value": "normal"},
    }
    
    if create_room_entity(ROOM_CONFIG, extra_attributes=room_extra_attrs):
        print(f"Created: {ROOM_CONFIG['id']}")
    else:
        print(f"Failed to create {ROOM_CONFIG['id']}")

    print(f"Creating AlertEvent entity: {ALERT_ID}")
    if create_alert_event(SCENARIO_ID, "critical", ROOM_CONFIG["id"]):
        print(f"Created: {ALERT_ID}")
    else:
        print(f"Failed to create {ALERT_ID}")

    print(f"Creating RobotAction entity: {ROBOT_ACTION_ID}")
    if create_robot_action(ROBOT_ACTION_ID, ROBOT_ID, ROOM_CONFIG["id"], scenario_id=SCENARIO_ID):
        print(f"Created: {ROBOT_ACTION_ID}")
    else:
        print(f"Failed to create {ROBOT_ACTION_ID}")
    
    # Hiển thị kết quả
    print_summary()

if __name__ == "__main__":
    main()