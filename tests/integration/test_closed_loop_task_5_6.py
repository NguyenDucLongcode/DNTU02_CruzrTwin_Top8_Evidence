import os
import pytest
import pandas as pd
import numpy as np
import json

from orchestration.pipeline import process_sensor_event
from src.ai.model_trainer import train_normal_boundary_model
from src.common.config import get_config

@pytest.fixture(scope="module", autouse=True)
def setup_integration_test_model(tmp_path_factory):
    # Temp directories
    tmp_dir = tmp_path_factory.mktemp("integration_test")
    data_path = tmp_dir / "sensor_data.csv"
    model_path = tmp_dir / "anomaly_model.pkl"
    schema_path = tmp_dir / "feature_schema.json"
    log_dir = tmp_dir / "logs"
    evidence_dir = tmp_dir / "evidence"
    
    log_dir.mkdir()
    evidence_dir.mkdir()
    
    # Generate proper normal and anomaly distributions with variance
    np.random.seed(42)
    
    # Normal data (100 rows)
    normal_temp = np.random.uniform(22, 30, 100)
    normal_hum = np.random.uniform(45, 70, 100)
    normal_smoke = np.random.uniform(20, 80, 100)
    normal_co2 = np.random.uniform(350, 500, 100)
    normal_power = np.random.uniform(30, 80, 100)
    normal_labels = np.zeros(100, dtype=int)
    
    # Anomaly data (10 rows)
    anom_temp = np.random.uniform(38, 50, 10)
    anom_hum = np.random.uniform(10, 25, 10)
    anom_smoke = np.random.uniform(300, 500, 10)
    anom_co2 = np.random.uniform(900, 1200, 10)
    anom_power = np.random.uniform(5, 15, 10)
    anom_labels = np.ones(10, dtype=int)
    
    df = pd.DataFrame({
        "timestamp": ["2026-06-08T12:00:00Z"] * 110,
        "temperature": np.concatenate([normal_temp, anom_temp]),
        "humidity": np.concatenate([normal_hum, anom_hum]),
        "smoke": np.concatenate([normal_smoke, anom_smoke]),
        "co2": np.concatenate([normal_co2, anom_co2]),
        "power": np.concatenate([normal_power, anom_power]),
        "label": np.concatenate([normal_labels, anom_labels])
    })
    df.to_csv(data_path, index=False)
    
    # Patch config before training
    import src.common.config
    original_get_config = src.common.config.get_config
    
    def mock_get_config():
        cfg = original_get_config()
        cfg["model_path"] = str(model_path)
        cfg["feature_schema_path"] = str(schema_path)
        cfg["log_dir"] = str(log_dir)
        cfg["evidence_dir"] = str(evidence_dir)
        return cfg
        
    src.common.config.get_config = mock_get_config
    
    # Train model (fits ONLY on label=0 normal data internally)
    train_normal_boundary_model(
        data_path=str(data_path),
        model_path=str(model_path),
        feature_schema_path=str(schema_path)
    )
    
    yield
    
    # Restore original config
    src.common.config.get_config = original_get_config

def test_closed_loop_normal():
    # Input normal reading
    sensor = {
        "temperature": 25.0,
        "humidity": 60.0,
        "smoke": 50.0,
        "co2": 400.0,
        "power": 50.0
    }
    res = process_sensor_event(sensor)
    
    # Assertions
    assert res["ai_result"]["predicted_level"] == "normal"
    assert res["ai_result"]["predicted_anomaly"] == 0
    assert res["alert_event"] is None

def test_closed_loop_warning():
    # Input warning reading
    sensor = {
        "temperature": 34.0,
        "humidity": 65.0,
        "smoke": 180.0,
        "co2": 750.0,
        "power": 90.0
    }
    res = process_sensor_event(sensor)
    
    # Assertions
    assert res["ai_result"]["predicted_level"] == "warning"
    assert res["ai_result"]["predicted_anomaly"] == 1
    assert res["alert_event"] is not None
    assert res["alert_event"]["level"] == "warning"
    assert res["alert_event"]["status"] == "OPEN"

def test_closed_loop_critical():
    # Input critical reading
    sensor = {
        "temperature": 45.0,
        "humidity": 15.0,
        "smoke": 400.0,
        "co2": 1000.0,
        "power": 8.0
    }
    res = process_sensor_event(sensor)
    
    # Assertions
    assert res["ai_result"]["predicted_level"] == "critical"
    assert res["ai_result"]["predicted_anomaly"] == 1
    assert res["alert_event"] is not None
    assert res["alert_event"]["level"] == "critical"
    assert res["alert_event"]["status"] == "OPEN"
    assert res["alert_event"]["action_code"] == "DISPATCH_CRUZR_GUIDANCE"
    assert "send cruzr" in res["alert_event"]["recommended_action"].lower()
