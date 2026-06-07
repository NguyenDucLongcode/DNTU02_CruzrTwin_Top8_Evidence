import os
import sys
from unittest.mock import patch, MagicMock

# Add project root to path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from src.orchestration.event_pipeline import process_room_state

# We mock all fiware client methods to keep integration tests offline-friendly
@patch("src.alerts.alert_service.get_entity")
@patch("src.alerts.alert_service.upsert_entity")
@patch("src.alerts.alert_service.update_entity_attrs")
@patch("src.robot.robot_action_service.get_entity")
@patch("src.robot.robot_action_service.upsert_entity")
@patch("src.robot.robot_action_service.update_entity_attrs")
@patch("src.orchestration.event_pipeline.get_entity")
def test_closed_loop_normal(mock_orch_get, mock_rob_patch, mock_rob_post, mock_rob_get, mock_al_patch, mock_al_post, mock_al_get):
    mock_orch_get.return_value = None
    
    room_state = {
        "demo_run_id": "RUN_001",
        "scenario_id": "SCN_NORMAL_01",
        "scenario_source": "payload",
        "zone_id": "A101",
        "temperature": 24.0,
        "humidity": 55.0,
        "air_quality_or_co2": 400,
        "smoke_status": 0,
        "energy_consumption": 340,
        "expected_label": "normal"
    }
    
    res = process_room_state(room_state)
    assert res["pipeline_status"] == "NO_ACTION"
    assert res["ai_result"]["predicted_level"] == "normal"
    assert res["alert_event"] == {}
    assert res["robot_action"] == {}

@patch("src.alerts.alert_service.get_entity")
@patch("src.alerts.alert_service.upsert_entity")
@patch("src.alerts.alert_service.update_entity_attrs")
@patch("src.robot.robot_action_service.get_entity")
@patch("src.robot.robot_action_service.upsert_entity")
@patch("src.robot.robot_action_service.update_entity_attrs")
@patch("src.orchestration.event_pipeline.get_entity")
def test_closed_loop_warning(mock_orch_get, mock_rob_patch, mock_rob_post, mock_rob_get, mock_al_patch, mock_al_post, mock_al_get):
    mock_orch_get.return_value = None
    mock_al_get.return_value = None
    mock_al_post.return_value = {"success": True}
    
    room_state = {
        "demo_run_id": "RUN_001",
        "scenario_id": "SCN_WARNING_01",
        "scenario_source": "payload",
        "zone_id": "A101",
        "temperature": 34.0,
        "humidity": 55.0,
        "air_quality_or_co2": 400,
        "smoke_status": 0,
        "energy_consumption": 340,
        "expected_label": "warning"
    }
    
    res = process_room_state(room_state)
    assert res["pipeline_status"] == "WARNING_ALERT_CREATED"
    assert res["ai_result"]["predicted_level"] == "warning"
    assert res["alert_event"]["id"] == "AlertEvent:RUN_001:SCN_WARNING_01"
    assert res["robot_action"] == {}

@patch("src.alerts.alert_service.get_entity")
@patch("src.alerts.alert_service.upsert_entity")
@patch("src.alerts.alert_service.update_entity_attrs")
@patch("src.robot.robot_action_service.get_entity")
@patch("src.robot.robot_action_service.upsert_entity")
@patch("src.robot.robot_action_service.update_entity_attrs")
@patch("src.orchestration.event_pipeline.get_entity")
def test_closed_loop_critical(mock_orch_get, mock_rob_patch, mock_rob_post, mock_rob_get, mock_al_patch, mock_al_post, mock_al_get):
    mock_orch_get.return_value = None
    mock_al_get.side_effect = [
        None,  # First call in create_alert_event
        {      # Second call in update_alert_status
            "id": "AlertEvent:RUN_001:SCN_CRITICAL_01",
            "status": {"value": "OPEN"},
            "level": {"value": "critical"},
            "demo_run_id": {"value": "RUN_001"},
            "scenario_id": {"value": "SCN_CRITICAL_01"},
            "scenario_source": {"value": "payload"},
            "zone_id": {"value": "A101"},
            "source_entity_id": {"value": "Room:A101"}
        }
    ]
    mock_al_post.return_value = {"success": True}
    mock_al_patch.return_value = {"success": True}
    mock_rob_post.return_value = {"success": True}
    mock_rob_patch.return_value = {"success": True}
    
    # Mock robot action state changes
    states = ["PENDING", "SENT_TO_BRIDGE", "IN_PROGRESS", "GUIDANCE_DELIVERED"]
    call_idx = [0]
    def get_side_effect(id):
        curr_state = states[min(call_idx[0], len(states)-1)]
        call_idx[0] += 1
        return {
            "id": id,
            "status": {"value": curr_state}
        }
    mock_rob_get.side_effect = get_side_effect
    
    room_state = {
        "demo_run_id": "RUN_001",
        "scenario_id": "SCN_CRITICAL_01",
        "scenario_source": "payload",
        "zone_id": "A101",
        "temperature": 40.0,
        "humidity": 75.0,
        "air_quality_or_co2": 400,
        "smoke_status": 1,
        "energy_consumption": 340,
        "expected_label": "critical"
    }
    
    res = process_room_state(room_state)
    assert res["pipeline_status"] == "CRITICAL_ALERT_AND_ROBOT_ACTION_CREATED"
    assert res["ai_result"]["predicted_level"] == "critical"
    assert res["alert_event"]["id"] == "AlertEvent:RUN_001:SCN_CRITICAL_01"
    assert res["robot_action"]["id"] == "RobotAction:RUN_001:SCN_CRITICAL_01:CRUZR_01"
    assert res["robot_action"]["status"] == "GUIDANCE_DELIVERED"
