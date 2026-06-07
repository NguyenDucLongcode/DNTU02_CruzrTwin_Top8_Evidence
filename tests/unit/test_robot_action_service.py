import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from src.robot.robot_action_service import create_robot_action, dispatch_robot_action, update_robot_action_status
from src.common.errors import ValidationError, RobotActionError

@patch("src.robot.robot_action_service.upsert_entity")
def test_create_robot_action_warning(mock_upsert):
    alert_event = {
        "id": "AlertEvent:RUN_001:SCN_01",
        "level": "warning"
    }
    res = create_robot_action(alert_event)
    assert res["status"] == "NO_ROBOT_ACTION_REQUIRED"
    mock_upsert.assert_not_called()

@patch("src.robot.robot_action_service.upsert_entity")
def test_create_robot_action_critical(mock_upsert):
    mock_upsert.return_value = {"success": True}
    alert_event = {
        "id": "AlertEvent:RUN_001:SCN_02",
        "level": "critical",
        "demo_run_id": "RUN_001",
        "scenario_id": "SCN_02",
        "scenario_source": "payload",
        "zone_id": "ROOM_101"
    }
    res = create_robot_action(alert_event)
    assert res["id"] == "RobotAction:RUN_001:SCN_02:CRUZR_01"
    assert res["status"] == "PENDING"
    assert "Room A101" in res["message_en"]
    mock_upsert.assert_called_once()

@patch("src.robot.robot_action_service.get_entity")
@patch("src.robot.robot_action_service.update_entity_attrs")
def test_robot_lifecycle_validation(mock_patch, mock_get):
    action_id = "RobotAction:RUN_001:SCN_02:CRUZR_01"
    mock_get.return_value = {
        "id": action_id,
        "status": {"value": "PENDING"}
    }
    mock_patch.return_value = {"success": True}
    
    # 1. Valid transition PENDING -> SENT_TO_BRIDGE
    res = update_robot_action_status(action_id, "SENT_TO_BRIDGE")
    assert res["status"] == "SENT_TO_BRIDGE"
    
    # 2. Invalid transition SENT_TO_BRIDGE -> ACKED (must go through IN_PROGRESS etc.)
    mock_get.return_value = {
        "id": action_id,
        "status": {"value": "SENT_TO_BRIDGE"}
    }
    with pytest.raises(ValidationError):
        update_robot_action_status(action_id, "ACKED")

@patch("src.robot.robot_action_service.get_adapter")
@patch("src.robot.robot_action_service.get_entity")
@patch("src.robot.robot_action_service.update_entity_attrs")
def test_dispatch_mock_adapter(mock_patch, mock_get, mock_get_adapter):
    action_id = "RobotAction:RUN_001:SCN_02:CRUZR_01"
    robot_action = {
        "id": action_id,
        "demo_run_id": "RUN_001",
        "scenario_id": "SCN_02",
        "scenario_source": "payload",
        "robot_id": "CRUZR_01",
        "alert_id": "AlertEvent:RUN_001:SCN_02",
        "zone_id": "ROOM_101",
        "action_type": "VOICE_DISPLAY_GUIDANCE",
        "navigation_mode": "PREDEFINED_RESPONSE_POINT",
        "target_location": "RESPONSE_POINT_A101",
        "message_en": "Critical",
        "message_vi": "Phát hiện",
        "status": "PENDING",
        "adapter": "MockCruzrAdapter"
    }
    
    mock_adapter = MagicMock()
    mock_adapter.dispatch.return_value = {"status": "GUIDANCE_DELIVERED"}
    mock_get_adapter.return_value = mock_adapter
    
    mock_get.return_value = {
        "id": action_id,
        "status": {"value": "PENDING"}
    }
    mock_patch.return_value = {"success": True}
    
    # Run dispatch
    # Since dispatch calls update_robot_action_status, we need mock_get to return appropriate status transitions
    # In order to simulate: PENDING -> SENT_TO_BRIDGE -> IN_PROGRESS -> GUIDANCE_DELIVERED
    states = ["PENDING", "SENT_TO_BRIDGE", "IN_PROGRESS", "GUIDANCE_DELIVERED"]
    call_idx = [0]
    def get_side_effect(id):
        curr_state = states[min(call_idx[0], len(states)-1)]
        call_idx[0] += 1
        return {
            "id": action_id,
            "status": {"value": curr_state}
        }
    mock_get.side_effect = get_side_effect
    
    res = dispatch_robot_action(robot_action)
    assert res["status"] == "GUIDANCE_DELIVERED"
