import os
import sys
import pytest

# Add project root to path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from src.ai.detector import detect_anomaly
from src.common.errors import ValidationError

def test_detector_schema_and_fields():
    reading = {
        "demo_run_id": "DNTU02_TOP8_RUN_2026_001",
        "scenario_id": "SCN_CRITICAL_001",
        "scenario_source": "payload",
        "zone_id": "DNTU_ROOM_A101",
        "timestamp": "2026-05-17T09:00:16Z",
        "source_entity_id": "Room:DNTU_ROOM_A101",
        "temperature": 39.8,
        "humidity": 78.0,
        "air_quality_or_co2": 1250,
        "smoke_status": 1,
        "energy_consumption": 920,
        "device_status": "ON",
        "expected_label": "critical"
    }
    
    res = detect_anomaly(reading)
    
    # Verify complete schema
    expected_fields = [
        "demo_run_id", "scenario_id", "scenario_source", "zone_id", "timestamp",
        "source_entity_id", "model", "features", "anomaly_score", "risk_score",
        "rule_level", "rule_hits", "rule_confidence", "predicted_level",
        "expected_label", "rationale", "recommended_action", "status"
    ]
    for field in expected_fields:
        assert field in res
        
    assert res["predicted_level"] == "critical"
    assert res["expected_label"] == "critical"
    assert res["recommended_action"] == "CREATE_CRITICAL_ALERT_AND_DISPATCH_CRUZR"

def test_detector_missing_fields():
    reading = {
        "demo_run_id": "DNTU02_TOP8_RUN_2026_001",
        # Missing scenario_id
        "scenario_source": "payload",
        "zone_id": "DNTU_ROOM_A101",
        "timestamp": "2026-05-17T09:00:16Z",
        "source_entity_id": "Room:DNTU_ROOM_A101",
        "temperature": 39.8,
        "humidity": 78.0,
        "air_quality_or_co2": 1250,
        "smoke_status": 1,
        "energy_consumption": 920,
        "device_status": "ON"
    }
    
    with pytest.raises(ValidationError):
        detect_anomaly(reading)

def test_detector_invalid_types():
    reading = {
        "demo_run_id": "DNTU02_TOP8_RUN_2026_001",
        "scenario_id": "SCN_CRITICAL_001",
        "scenario_source": "payload",
        "zone_id": "DNTU_ROOM_A101",
        "timestamp": "2026-05-17T09:00:16Z",
        "source_entity_id": "Room:DNTU_ROOM_A101",
        "temperature": "very hot", # invalid type
        "humidity": 78.0,
        "air_quality_or_co2": 1250,
        "smoke_status": 1,
        "energy_consumption": 920,
        "device_status": "ON"
    }
    
    with pytest.raises(ValidationError):
        detect_anomaly(reading)

def test_no_overclaim_model_name():
    # If the model does not exist, it should fallback to explainable rule assisted mode
    reading = {
        "demo_run_id": "DNTU02_TOP8_RUN_2026_001",
        "scenario_id": "SCN_NORMAL_001",
        "scenario_source": "payload",
        "zone_id": "DNTU_ROOM_A101",
        "timestamp": "2026-05-17T09:00:16Z",
        "source_entity_id": "Room:DNTU_ROOM_A101",
        "temperature": 24.5,
        "humidity": 52.0,
        "air_quality_or_co2": 410,
        "smoke_status": 0,
        "energy_consumption": 340,
        "device_status": "ON"
    }
    res = detect_anomaly(reading)
    # Since we didn't mock file check here, if models/isolation_forest.joblib does not exist it must say explainable_rule_assisted_anomaly_layer
    assert res["model"] in ["explainable_rule_assisted_anomaly_layer", "rule_assisted_isolation_forest"]
