import os
import json
import pytest
from src.alerts.alert_service import create_alert_event

@pytest.fixture(autouse=True)
def patch_logs_dir(tmp_path):
    import src.common.config
    original_get_config = src.common.config.get_config
    
    # Create temp logs and evidence dirs
    log_dir = tmp_path / "logs"
    evidence_dir = tmp_path / "evidence"
    log_dir.mkdir()
    evidence_dir.mkdir()
    
    def mock_get_config():
        cfg = original_get_config()
        cfg["log_dir"] = str(log_dir)
        cfg["evidence_dir"] = str(evidence_dir)
        return cfg
        
    src.common.config.get_config = mock_get_config
    yield
    src.common.config.get_config = original_get_config

def test_alert_service_normal():
    # Normal result should not produce alert
    ai_result = {
        "timestamp": "2026-06-08T12:00:00Z",
        "predicted_anomaly": 0,
        "predicted_level": "normal",
        "anomaly_score": 0.15
    }
    event = create_alert_event(ai_result)
    assert event is None

def test_alert_service_warning():
    # Warning result should produce alert
    ai_result = {
        "timestamp": "2026-06-08T12:00:10Z",
        "predicted_anomaly": 1,
        "predicted_level": "warning",
        "anomaly_score": -0.18
    }
    event = create_alert_event(ai_result)
    assert event is not None
    assert event["level"] == "warning"
    assert event["status"] == "OPEN"
    assert "Warning" in event["message"]
    
    # Check that it log correctly to log_dir
    import src.common.config
    log_path = os.path.join(src.common.config.get_config()["log_dir"], "alert_events.jsonl")
    assert os.path.exists(log_path)
    with open(log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 1
        log_data = json.loads(lines[0])
        assert log_data["level"] == "warning"
        assert log_data["ai_result_ref"]["predicted_anomaly"] == 1

def test_alert_service_critical():
    # Critical result should produce alert
    ai_result = {
        "timestamp": "2026-06-08T12:00:20Z",
        "predicted_anomaly": 1,
        "predicted_level": "critical",
        "anomaly_score": -0.35
    }
    event = create_alert_event(ai_result)
    assert event is not None
    assert event["level"] == "critical"
    assert event["status"] == "OPEN"
    assert "Critical" in event["message"]
    assert event["recommended_action"] == "DISPATCH_CRUZR_GUIDANCE"
