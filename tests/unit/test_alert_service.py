import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from src.alerts.alert_service import create_alert_event, update_alert_status, build_alert_id
from src.common.errors import ValidationError, AlertServiceError

# Mock Orion Client calls
@patch("src.alerts.alert_service.get_entity")
@patch("src.alerts.alert_service.upsert_entity")
def test_create_alert_normal(mock_upsert, mock_get):
    ai_result = {"predicted_level": "normal"}
    res = create_alert_event(ai_result, {})
    assert res["status"] == "NO_ALERT"
    mock_upsert.assert_not_called()

@patch("src.alerts.alert_service.get_entity")
@patch("src.alerts.alert_service.upsert_entity")
def test_create_alert_warning(mock_upsert, mock_get):
    mock_get.return_value = None
    mock_upsert.return_value = {"success": True}
    
    ai_result = {
        "predicted_level": "warning",
        "demo_run_id": "RUN_001",
        "scenario_id": "SCN_01",
        "scenario_source": "payload",
        "zone_id": "ROOM_101",
        "source_entity_id": "Room:101",
        "recommended_action": "CREATE_WARNING_ALERT",
        "model": "model_x",
        "anomaly_score": -0.18,
        "rationale": "temp warning",
        "features": {
            "temperature": 33.0,
            "humidity": 60.0,
            "air_quality_or_co2": 400,
            "smoke_status": 0,
            "energy_consumption": 300
        }
    }
    
    res = create_alert_event(ai_result, {})
    assert res["id"] == "AlertEvent:RUN_001:SCN_01"
    assert res["level"] == "warning"
    assert res["status"] == "OPEN"
    assert res["recommended_action"] == "SHOW_DASHBOARD_WARNING"
    mock_upsert.assert_called_once()

@patch("src.alerts.alert_service.get_entity")
@patch("src.alerts.alert_service.upsert_entity")
def test_create_alert_critical(mock_upsert, mock_get):
    mock_get.return_value = None
    mock_upsert.return_value = {"success": True}
    
    ai_result = {
        "predicted_level": "critical",
        "demo_run_id": "RUN_001",
        "scenario_id": "SCN_02",
        "scenario_source": "payload",
        "zone_id": "ROOM_101",
        "source_entity_id": "Room:101",
        "recommended_action": "CREATE_CRITICAL_ALERT_AND_DISPATCH_CRUZR",
        "model": "model_x",
        "anomaly_score": -0.31,
        "rationale": "smoke detected",
        "features": {
            "temperature": 40.0,
            "humidity": 60.0,
            "air_quality_or_co2": 1300,
            "smoke_status": 1,
            "energy_consumption": 300
        }
    }
    
    res = create_alert_event(ai_result, {})
    assert res["id"] == "AlertEvent:RUN_001:SCN_02"
    assert res["level"] == "critical"
    assert res["status"] == "OPEN"
    assert res["recommended_action"] == "DISPATCH_CRUZR_GUIDANCE"
    mock_upsert.assert_called_once()

@patch("src.alerts.alert_service.get_entity")
@patch("src.alerts.alert_service.update_entity_attrs")
def test_alert_service_idempotency(mock_patch, mock_get):
    alert_id = "AlertEvent:RUN_001:SCN_02"
    mock_get.return_value = {
        "id": alert_id,
        "type": "AlertEvent",
        "status": {"value": "OPEN"},
        "created_at": {"value": "2026-06-07T00:00:00Z"}
    }
    mock_patch.return_value = {"success": True}
    
    ai_result = {
        "predicted_level": "critical",
        "demo_run_id": "RUN_001",
        "scenario_id": "SCN_02",
        "scenario_source": "payload",
        "zone_id": "ROOM_101",
        "source_entity_id": "Room:101",
        "recommended_action": "CREATE_CRITICAL_ALERT_AND_DISPATCH_CRUZR",
        "model": "model_x",
        "anomaly_score": -0.31,
        "rationale": "smoke detected updated",
        "features": {
            "temperature": 41.0,
            "humidity": 60.0,
            "air_quality_or_co2": 1300,
            "smoke_status": 1,
            "energy_consumption": 300
        }
    }
    
    res = create_alert_event(ai_result, {})
    assert res["id"] == alert_id
    assert res["status"] == "OPEN"  # status unchanged
    mock_patch.assert_called_once()

@patch("src.alerts.alert_service.get_entity")
@patch("src.alerts.alert_service.update_entity_attrs")
def test_alert_lifecycle_validation(mock_patch, mock_get):
    alert_id = "AlertEvent:RUN_001:SCN_02"
    
    # 1. Valid transition OPEN -> DISPATCHED
    mock_get.return_value = {
        "id": alert_id,
        "status": {"value": "OPEN"}
    }
    mock_patch.return_value = {"success": True}
    res = update_alert_status(alert_id, "DISPATCHED")
    assert res["status"] == "DISPATCHED"
    
    # 2. Invalid transition RESOLVED -> OPEN (without note)
    mock_get.return_value = {
        "id": alert_id,
        "status": {"value": "RESOLVED"}
    }
    with pytest.raises(ValidationError):
        update_alert_status(alert_id, "OPEN")
        
    # 3. Invalid transition RESOLVED -> OPEN with recovery note is allowed
    res = update_alert_status(alert_id, "OPEN", note="recovery testing")
    assert res["status"] == "OPEN"
