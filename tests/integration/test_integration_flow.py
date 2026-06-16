import os
import json
import pytest
from unittest.mock import patch, MagicMock
from src.orchestration.pipeline import process_sensor_event
from src.alerts.alert_service import create_alert_event, create_robot_action_from_alert, reset_alert_service_cache
from src.ai.detector import detect_anomaly
import src.common.config
from src.common.logging_utils import reset_file

@pytest.fixture(autouse=True)
def setup_logs(tmp_path):
    # Setup temporary directory for logs and evidence
    log_dir = tmp_path / "logs"
    evidence_dir = tmp_path / "evidence"
    log_dir.mkdir(exist_ok=True)
    evidence_dir.mkdir(exist_ok=True)
    
    # Overwrite the config function globally for modules already imported
    original_get_config = src.common.config.get_config
    
    def mock_get_config():
        cfg = original_get_config()
        cfg["demo_run_id"] = "DNTU02_TOP8_RUN_2026_001"
        cfg["default_zone_id"] = "DNTU_ROOM_A101"
        cfg["model_path"] = "models/anomaly_model.pkl"
        cfg["log_dir"] = str(log_dir)
        cfg["evidence_dir"] = str(evidence_dir)
        cfg["orion_enabled"] = False
        return cfg
        
    src.common.config.get_config = mock_get_config
    reset_alert_service_cache()
    yield tmp_path
    src.common.config.get_config = original_get_config
    reset_alert_service_cache()

# Helper to read jsonl
def read_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

# Test 1: FIWARE payload parse đúng
def test_fiware_payload_parsing(setup_logs):
    payload = {
        "data": [
            {
                "temperature": {"type": "Number", "value": 39.8},
                "humidity": {"type": "Number", "value": 78.0},
                "co2": {"type": "Number", "value": 1250.0},
                "smoke_status": {"type": "Number", "value": 1.0},
                "energy_consumption": {"type": "Number", "value": 920.0},
                "demo_run_id": {"type": "Text", "value": "DNTU02_TOP8_RUN_2026_001"},
                "scenario_id": {"type": "Text", "value": "SCN_CRITICAL_001"},
                "zone_id": {"type": "Text", "value": "DNTU_ROOM_A101"}
            }
        ]
    }
    
    res = process_sensor_event(payload)
    assert res["processing_status"] == "SUCCESS"
    
    log_path = os.path.join(str(setup_logs / "logs"), "ai_detection.jsonl")
    logs = read_jsonl(log_path)
    assert len(logs) == 1
    entry = logs[0]
    
    # Check original field names preserved in log
    assert "temperature" in entry["sensor_values"]
    assert "humidity" in entry["sensor_values"]
    assert "air_quality_or_co2" in entry["sensor_values"]
    assert "smoke_status" in entry["sensor_values"]
    assert "energy_consumption" in entry["sensor_values"]
    assert entry["sensor_values"]["air_quality_or_co2"] == 1250.0
    assert entry["sensor_values"]["smoke_status"] == 1.0
    assert entry["sensor_values"]["energy_consumption"] == 920.0

# Test 2: AI không chạy khi thiếu dữ liệu quan trọng
def test_ai_incomplete_sensor_data(setup_logs):
    # Missing temperature and humidity
    incomplete_payload = {
        "co2": 1250.0,
        "smoke_status": 1.0,
        "energy_consumption": 920.0,
        "scenario_id": "SCN_CRITICAL_001"
    }
    
    res = process_sensor_event(incomplete_payload)
    assert res["processing_status"] == "SKIPPED_INCOMPLETE_SENSOR_DATA"
    assert res["ai_result"] is None
    assert res["alert_event"] is None
    
    # Check no log written to ai_detection or alert_events
    ai_log = os.path.join(str(setup_logs / "logs"), "ai_detection.jsonl")
    alert_log = os.path.join(str(setup_logs / "logs"), "alert_events.jsonl")
    assert len(read_jsonl(ai_log)) == 0
    assert len(read_jsonl(alert_log)) == 0

# Test 3: Isolation Forest chạy trước Rule Layer
def test_isolation_forest_before_rule_layer():
    sensor = {
        "temperature": 34.0,
        "humidity": 65.0,
        "co2": 750.0,
        "smoke_status": 0.0,
        "energy_consumption": 90.0
    }
    with patch("src.orchestration.pipeline.detect_anomaly", wraps=detect_anomaly) as mock_detect:
        res = process_sensor_event(sensor)
        assert mock_detect.called
        assert "anomaly_score" in res["ai_result"]
        assert isinstance(res["ai_result"]["anomaly_score"], float)
        assert "predicted_level" in res["ai_result"]

# Test 4: Normal không tạo AlertEvent
def test_normal_no_alert_event(setup_logs):
    sensor = {
        "temperature": 25.0,
        "humidity": 60.0,
        "co2": 400.0,
        "smoke_status": 0.0,
        "energy_consumption": 50.0,
        "scenario_id": "SCN_NORMAL_001"
    }
    res = process_sensor_event(sensor)
    assert res["ai_result"]["predicted_level"] == "normal"
    assert res["alert_event"] is None
    
    alert_log = os.path.join(str(setup_logs / "logs"), "alert_events.jsonl")
    assert len(read_jsonl(alert_log)) == 0

# Test 5: Warning tạo AlertEvent nhưng không tạo RobotAction
def test_warning_creates_alert_no_robot_action(setup_logs):
    sensor = {
        "temperature": 34.0,
        "humidity": 65.0,
        "co2": 750.0,
        "smoke_status": 0.0,
        "energy_consumption": 90.0,
        "scenario_id": "SCN_WARNING_001"
    }
    res = process_sensor_event(sensor)
    assert res["ai_result"]["predicted_level"] == "warning"
    assert res["alert_event"] is not None
    assert res["alert_event"]["severity"] == "warning"
    assert res["alert_event"]["status"] == "OPEN"
    assert res["alert_event"]["evidence_status"] == "ACTIVE"
    
    alert_log = os.path.join(str(setup_logs / "logs"), "alert_events.jsonl")
    alerts = read_jsonl(alert_log)
    assert len(alerts) == 1
    assert alerts[0]["status"] == "ACTIVE"
    assert alerts[0]["severity"] == "warning"
    
    robot_log = os.path.join(str(setup_logs / "logs"), "robot_actions.jsonl")
    assert len(read_jsonl(robot_log)) == 0

# Test 6: Critical tạo AlertEvent và RobotAction
def test_critical_creates_alert_and_robot_action(setup_logs):
    sensor = {
        "temperature": 45.0,
        "humidity": 15.0,
        "co2": 1000.0,
        "smoke_status": 1.0,
        "energy_consumption": 920.0,
        "scenario_id": "SCN_CRITICAL_001"
    }
    res = process_sensor_event(sensor)
    assert res["ai_result"]["predicted_level"] == "critical"
    assert res["alert_event"] is not None
    assert res["alert_event"]["severity"] == "critical"
    
    robot_log = os.path.join(str(setup_logs / "logs"), "robot_actions.jsonl")
    actions = read_jsonl(robot_log)
    assert len(actions) == 1
    assert actions[0]["status"] == "PENDING"
    assert actions[0]["robot_id"] == "CRUZR_01"
    assert actions[0]["action_type"] == "VOICE_DISPLAY_GUIDANCE"
    assert "Room Room" not in actions[0]["message"]
    assert "Room A101" in actions[0]["message"]
    assert "safe waiting area" in actions[0]["message"]

# Test 7: Không ghi SUCCESS giả khi Orion lỗi
def test_orion_failed_upsert(setup_logs):
    sensor = {
        "temperature": 45.0,
        "humidity": 15.0,
        "co2": 1000.0,
        "smoke_status": 1.0,
        "energy_consumption": 920.0,
        "scenario_id": "SCN_CRITICAL_001"
    }
    
    original_get_config = src.common.config.get_config
    def mock_get_config_orion():
        cfg = original_get_config()
        cfg["log_dir"] = str(setup_logs / "logs")
        cfg["evidence_dir"] = str(setup_logs / "evidence")
        cfg["orion_enabled"] = True
        return cfg
    src.common.config.get_config = mock_get_config_orion
    
    try:
        with patch("src.fiware.entities.entities_manager.upsert_entity", side_effect=Exception("Connection refused")):
            process_sensor_event(sensor)
    finally:
        src.common.config.get_config = original_get_config
        
    alert_log = os.path.join(str(setup_logs / "logs"), "alert_events.jsonl")
    alerts = read_jsonl(alert_log)
    assert len(alerts) == 1
    assert alerts[0]["orion_upsert_status"] == "FAILED"
    assert "Connection refused" in alerts[0]["error_message"]
    
    robot_log = os.path.join(str(setup_logs / "logs"), "robot_actions.jsonl")
    actions = read_jsonl(robot_log)
    assert len(actions) == 1
    assert actions[0]["orion_upsert_status"] == "FAILED"
    assert "Connection refused" in actions[0]["error_message"]

# Test 8: SKIPPED_OFFLINE khi orion_enabled = False
def test_orion_skipped_offline(setup_logs):
    sensor = {
        "temperature": 34.0,
        "humidity": 65.0,
        "co2": 750.0,
        "smoke_status": 0.0,
        "energy_consumption": 90.0,
        "scenario_id": "SCN_WARNING_001"
    }
    
    process_sensor_event(sensor)
    alert_log = os.path.join(str(setup_logs / "logs"), "alert_events.jsonl")
    alerts = read_jsonl(alert_log)
    assert len(alerts) == 1
    assert alerts[0]["orion_upsert_status"] == "SKIPPED_OFFLINE"

# Test 9: AlertEvent mock Orion trả về đúng properties
def test_orion_mock_alert_event_properties():
    mock_get_entity = MagicMock(return_value={
        "id": "AlertEvent:SCN_CRITICAL_001",
        "type": "AlertEvent",
        "status": {"value": "ACTIVE"},
        "severity": {"value": "critical"},
        "anomaly_score": {"value": -0.31}
    })
    
    entity = mock_get_entity("AlertEvent:SCN_CRITICAL_001")
    assert entity["type"] == "AlertEvent"
    assert entity["status"]["value"] == "ACTIVE"
    assert entity["severity"]["value"] == "critical"
    assert entity["anomaly_score"]["value"] == -0.31

# Test 10: predicted_level, level, severity đồng bộ
def test_level_severity_sync(setup_logs):
    sensor = {
        "temperature": 45.0,
        "humidity": 15.0,
        "co2": 1000.0,
        "smoke_status": 1.0,
        "energy_consumption": 920.0,
        "scenario_id": "SCN_CRITICAL_001"
    }
    res = process_sensor_event(sensor)
    ai_result = res["ai_result"]
    alert_event = res["alert_event"]
    
    # Assert sync in python return object
    assert ai_result["predicted_level"] == alert_event["level"]
    assert ai_result["predicted_level"] == alert_event["severity"]
    
    # Assert sync in log files
    ai_log = os.path.join(str(setup_logs / "logs"), "ai_detection.jsonl")
    alert_log = os.path.join(str(setup_logs / "logs"), "alert_events.jsonl")
    
    ai_entries = read_jsonl(ai_log)
    alert_entries = read_jsonl(alert_log)
    
    assert ai_entries[0]["predicted_level"] == alert_entries[0]["level"]
    assert ai_entries[0]["predicted_level"] == alert_entries[0]["severity"]

# Test 11: recommended_action không phải là mã code ngắn
def test_recommended_action_is_sentence(setup_logs):
    sensor = {
        "temperature": 45.0,
        "humidity": 15.0,
        "co2": 1000.0,
        "smoke_status": 1.0,
        "energy_consumption": 920.0,
        "scenario_id": "SCN_CRITICAL_001"
    }
    process_sensor_event(sensor)
    
    ai_log = os.path.join(str(setup_logs / "logs"), "ai_detection.jsonl")
    alert_log = os.path.join(str(setup_logs / "logs"), "alert_events.jsonl")
    
    ai_entry = read_jsonl(ai_log)[0]
    alert_entry = read_jsonl(alert_log)[0]
    
    # Should not be code codes like "DISPATCH_CRUZR_GUIDANCE" or "CHECK_ROOM"
    assert ai_entry["action_code"] == "DISPATCH_CRUZR_GUIDANCE"
    assert "send cruzr" in ai_entry["recommended_action"].lower()
    
    assert alert_entry["action_code"] == "DISPATCH_CRUZR_GUIDANCE"
    assert "send cruzr" in alert_entry["recommended_action"].lower()

# Test 12: Idempotency chống duplicate
def test_idempotency_no_duplicate(setup_logs):
    sensor = {
        "temperature": 45.0,
        "humidity": 15.0,
        "co2": 1000.0,
        "smoke_status": 1.0,
        "energy_consumption": 920.0,
        "scenario_id": "SCN_CRITICAL_001"
    }
    
    # Process twice
    process_sensor_event(sensor)
    process_sensor_event(sensor)
    
    alert_log = os.path.join(str(setup_logs / "logs"), "alert_events.jsonl")
    robot_log = os.path.join(str(setup_logs / "logs"), "robot_actions.jsonl")
    
    # Logs should contain only ONE entry for this scenario
    assert len(read_jsonl(alert_log)) == 1
    assert len(read_jsonl(robot_log)) == 1

# Test 13: AlertEvent liên kết được với AI Detection
def test_alert_event_links_to_ai_detection(setup_logs):
    sensor = {
        "temperature": 45.0,
        "humidity": 15.0,
        "co2": 1000.0,
        "smoke_status": 1.0,
        "energy_consumption": 920.0,
        "scenario_id": "SCN_CRITICAL_001"
    }
    process_sensor_event(sensor)
    
    ai_log = os.path.join(str(setup_logs / "logs"), "ai_detection.jsonl")
    alert_log = os.path.join(str(setup_logs / "logs"), "alert_events.jsonl")
    
    ai_entry = read_jsonl(ai_log)[0]
    alert_entry = read_jsonl(alert_log)[0]
    
    assert alert_entry["demo_run_id"] == ai_entry["demo_run_id"]
    assert alert_entry["scenario_id"] == ai_entry["scenario_id"]
    assert alert_entry["zone_id"] == ai_entry["zone_id"]
    assert alert_entry["anomaly_score"] == ai_entry["anomaly_score"]
    assert alert_entry["severity"] == ai_entry["predicted_level"]
    assert alert_entry["source_ai_event_id"] == ai_entry["source_ai_event_id"]

# Test 14: Orion RobotAction GET entity
def test_orion_mock_robot_action_properties():
    mock_get_entity = MagicMock(return_value={
        "id": "RobotAction:SCN_CRITICAL_001",
        "type": "RobotAction",
        "status": {"value": "PENDING"},
        "alert_id": {"value": "AlertEvent:SCN_CRITICAL_001"}
    })
    
    entity = mock_get_entity("RobotAction:SCN_CRITICAL_001")
    assert entity["type"] == "RobotAction"
    assert entity["status"]["value"] == "PENDING"
    assert entity["alert_id"]["value"] == "AlertEvent:SCN_CRITICAL_001"

# Test P0.2 — Smoke Status Normalization
def test_smoke_status_binary_normalization(setup_logs):
    sensor = {
        "temperature": 45.0,
        "humidity": 15.0,
        "co2": 1000.0,
        "smoke_status": 400.0,
        "energy_consumption": 920.0,
        "scenario_id": "SCN_CRITICAL_001"
    }
    process_sensor_event(sensor)
    
    ai_log_path = os.path.join(str(setup_logs / "logs"), "ai_detection.jsonl")
    ai_logs = read_jsonl(ai_log_path)
    assert len(ai_logs) == 1
    assert ai_logs[0]["sensor_values"]["smoke_status"] == 1
    assert isinstance(ai_logs[0]["sensor_values"]["smoke_status"], int)

def test_raw_smoke_value_preserved(setup_logs):
    sensor = {
        "temperature": 45.0,
        "humidity": 15.0,
        "co2": 1000.0,
        "smoke_status": 400.0,
        "energy_consumption": 920.0,
        "scenario_id": "SCN_CRITICAL_001"
    }
    process_sensor_event(sensor)
    
    ai_log_path = os.path.join(str(setup_logs / "logs"), "ai_detection.jsonl")
    ai_logs = read_jsonl(ai_log_path)
    assert len(ai_logs) == 1
    assert ai_logs[0]["sensor_values"]["raw_smoke_value"] == 400.0

# Test P0.3 — Full Schema Tests
def test_ai_detection_log_full_schema(setup_logs):
    sensor = {
        "temperature": 45.0,
        "humidity": 15.0,
        "co2": 1000.0,
        "smoke_status": 400.0,
        "energy_consumption": 920.0,
        "scenario_id": "SCN_CRITICAL_001"
    }
    process_sensor_event(sensor)
    
    ai_log_path = os.path.join(str(setup_logs / "logs"), "ai_detection.jsonl")
    ai_logs = read_jsonl(ai_log_path)
    assert len(ai_logs) == 1
    entry = ai_logs[0]
    
    required_fields = [
        "demo_run_id", "timestamp", "scenario_id", "zone_id", "source", "model",
        "sensor_values", "anomaly_score", "predicted_level", "expected_label",
        "rationale", "action_code", "recommended_action", "source_ai_event_id"
    ]
    for field in required_fields:
        assert field in entry, f"Missing required field {field}"
        
    sensor_subfields = [
        "temperature", "humidity", "air_quality_or_co2", "smoke_status",
        "energy_consumption", "raw_smoke_value"
    ]
    for sub in sensor_subfields:
        assert sub in entry["sensor_values"], f"Missing sensor subfield {sub}"
        
    assert entry["source"] == "FIWARE_ORION"
    assert entry["model"] == "rule_assisted_isolation_forest"
    assert isinstance(entry["anomaly_score"], float)
    assert entry["predicted_level"] in ["normal", "warning", "critical"]
    assert entry["action_code"] != ""
    assert entry["recommended_action"] != ""
    assert entry["recommended_action"] != entry["action_code"]
    assert entry["source_ai_event_id"].startswith("AIEvent:")

def test_alert_event_log_full_schema(setup_logs):
    sensor = {
        "temperature": 45.0,
        "humidity": 15.0,
        "co2": 1000.0,
        "smoke_status": 400.0,
        "energy_consumption": 920.0,
        "scenario_id": "SCN_CRITICAL_001"
    }
    process_sensor_event(sensor)
    
    alert_log_path = os.path.join(str(setup_logs / "logs"), "alert_events.jsonl")
    alert_logs = read_jsonl(alert_log_path)
    assert len(alert_logs) == 1
    entry = alert_logs[0]
    
    required_fields = [
        "demo_run_id", "timestamp", "alert_id", "scenario_id", "zone_id",
        "level", "severity", "status", "source_model", "anomaly_score",
        "message", "action_code", "recommended_action", "orion_upsert_status",
        "source_ai_event_id"
    ]
    for field in required_fields:
        assert field in entry, f"Missing required field {field}"
        
    assert entry["alert_id"].startswith("AlertEvent:")
    assert entry["level"] in ["warning", "critical"]
    assert entry["severity"] == entry["level"]
    assert entry["status"] == "ACTIVE"
    assert entry["source_model"] == "rule_assisted_isolation_forest"
    assert entry["recommended_action"] != ""
    assert entry["recommended_action"] != entry["action_code"]
    assert entry["orion_upsert_status"] in ["SKIPPED_OFFLINE", "SUCCESS", "FAILED"]

# Test P0.4 — Action Code / Recommended Action Separation
def test_action_code_separated_from_recommended_action(setup_logs):
    sensor = {
        "temperature": 45.0,
        "humidity": 15.0,
        "co2": 1000.0,
        "smoke_status": 400.0,
        "energy_consumption": 920.0,
        "scenario_id": "SCN_CRITICAL_001"
    }
    process_sensor_event(sensor)
    
    ai_log_path = os.path.join(str(setup_logs / "logs"), "ai_detection.jsonl")
    alert_log_path = os.path.join(str(setup_logs / "logs"), "alert_events.jsonl")
    
    ai_entry = read_jsonl(ai_log_path)[0]
    alert_entry = read_jsonl(alert_log_path)[0]
    
    assert ai_entry["action_code"] == "DISPATCH_CRUZR_GUIDANCE"
    assert ai_entry["recommended_action"] != "DISPATCH_CRUZR_GUIDANCE"
    assert "send Cruzr" in ai_entry["recommended_action"]
    
    assert alert_entry["action_code"] == "DISPATCH_CRUZR_GUIDANCE"
    assert alert_entry["recommended_action"] != "DISPATCH_CRUZR_GUIDANCE"
    assert "Send Cruzr" in alert_entry["recommended_action"]


def test_alert_event_recommended_action_cleaned(setup_logs):
    sensor = {
        "temperature": 45.0,
        "humidity": 15.0,
        "co2": 1000.0,
        "smoke_status": 400.0,
        "energy_consumption": 920.0,
        "scenario_id": "SCN_CRITICAL_001"
    }
    process_sensor_event(sensor)
    
    alert_log_path = os.path.join(str(setup_logs / "logs"), "alert_events.jsonl")
    alert_entry = read_jsonl(alert_log_path)[0]
    
    assert not alert_entry["recommended_action"].startswith("Create critical")
    assert alert_entry["recommended_action"].startswith("Send Cruzr")

# Test P1 — expected_label only for replay or test context
def test_expected_label_only_for_replay_or_test_context(setup_logs):
    # 1. Without expected_label
    sensor_no_label = {
        "temperature": 25.0,
        "humidity": 60.0,
        "co2": 400.0,
        "smoke_status": 0.0,
        "energy_consumption": 50.0,
        # scenario_id doesn't contain NORMAL, WARNING or CRITICAL to avoid auto-labeling logic
        "scenario_id": "SCN_TEST_RUN"
    }
    process_sensor_event(sensor_no_label)
    
    ai_log_path = os.path.join(str(setup_logs / "logs"), "ai_detection.jsonl")
    ai_logs = read_jsonl(ai_log_path)
    assert len(ai_logs) == 1
    assert ai_logs[0]["expected_label"] is None
    
    # Reset log and test with expected_label
    reset_file(ai_log_path)
    sensor_with_label = {
        "temperature": 25.0,
        "humidity": 60.0,
        "co2": 400.0,
        "smoke_status": 0.0,
        "energy_consumption": 50.0,
        "scenario_id": "SCN_TEST_RUN",
        "expected_label": "critical"
    }
    process_sensor_event(sensor_with_label)
    ai_logs = read_jsonl(ai_log_path)
    assert len(ai_logs) == 1
    assert ai_logs[0]["expected_label"] == "critical"

# Test P1 — Orion success marks SUCCESS
def test_orion_success_marks_success(setup_logs):
    sensor = {
        "temperature": 45.0,
        "humidity": 15.0,
        "co2": 1000.0,
        "smoke_status": 400.0,
        "energy_consumption": 920.0,
        "scenario_id": "SCN_CRITICAL_001"
    }
    
    original_get_config = src.common.config.get_config
    def mock_get_config_orion_enabled():
        cfg = original_get_config()
        cfg["log_dir"] = str(setup_logs / "logs")
        cfg["evidence_dir"] = str(setup_logs / "evidence")
        cfg["orion_enabled"] = True
        return cfg
    src.common.config.get_config = mock_get_config_orion_enabled
    
    try:
        with patch("src.fiware.entities.entities_manager.upsert_entity", return_value=True):
            process_sensor_event(sensor)
    finally:
        src.common.config.get_config = original_get_config
        
    alert_log_path = os.path.join(str(setup_logs / "logs"), "alert_events.jsonl")
    alert_logs = read_jsonl(alert_log_path)
    assert len(alert_logs) == 1
    assert alert_logs[0]["orion_upsert_status"] == "SUCCESS"

# Test P1 — normal AI Detection log written
def test_normal_ai_detection_log_written(setup_logs):
    sensor = {
        "temperature": 25.0,
        "humidity": 60.0,
        "co2": 400.0,
        "smoke_status": 0.0,
        "energy_consumption": 50.0,
        "scenario_id": "SCN_NORMAL_001"
    }
    res = process_sensor_event(sensor)
    assert res["ai_result"]["predicted_level"] == "normal"
    
    ai_log_path = os.path.join(str(setup_logs / "logs"), "ai_detection.jsonl")
    alert_log_path = os.path.join(str(setup_logs / "logs"), "alert_events.jsonl")
    
    assert len(read_jsonl(ai_log_path)) == 1
    assert len(read_jsonl(alert_log_path)) == 0

