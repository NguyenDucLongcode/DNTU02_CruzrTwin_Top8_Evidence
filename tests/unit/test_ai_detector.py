import os
import pytest
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib

from src.ai.detector import detect_anomaly
from src.ai.model_trainer import train_normal_boundary_model
from src.common.config import get_config

@pytest.fixture(scope="module", autouse=True)
def setup_test_model(tmp_path_factory):
    # Set up temporary directory for model and evidence
    tmp_dir = tmp_path_factory.mktemp("detector_test")
    data_path = tmp_dir / "sensor_data.csv"
    model_path = tmp_dir / "anomaly_model.pkl"
    schema_path = tmp_dir / "feature_schema.json"
    evidence_dir = tmp_dir / "evidence"
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
    
    # Patch config first so that train_normal_boundary_model writes to temp evidence dir
    import src.common.config
    original_get_config = src.common.config.get_config
    
    def mock_get_config():
        cfg = original_get_config()
        cfg["model_path"] = str(model_path)
        cfg["feature_schema_path"] = str(schema_path)
        cfg["evidence_dir"] = str(evidence_dir)
        return cfg
        
    src.common.config.get_config = mock_get_config
    
    # Train model
    train_normal_boundary_model(
        data_path=str(data_path),
        model_path=str(model_path),
        feature_schema_path=str(schema_path)
    )
    
    yield
    
    # Restore original config
    src.common.config.get_config = original_get_config

def test_detector_normal():
    sensor = {
        "temperature": 25.0,
        "humidity": 50.0,
        "smoke": 40.0,
        "co2": 400.0,
        "power": 50.0
    }
    res = detect_anomaly(sensor)
    assert res["predicted_anomaly"] == 0
    assert res["predicted_level"] == "normal"
    assert res["in_boundary"] is True
    assert res["recommended_action"] == "NO_ACTION"

def test_detector_warning():
    # Outside normal boundaries -> predicted_anomaly = 1, rule says warning
    sensor = {
        "temperature": 34.0,
        "humidity": 65.0,
        "smoke": 180.0,
        "co2": 750.0,
        "power": 90.0
    }
    res = detect_anomaly(sensor)
    assert res["predicted_anomaly"] == 1
    assert res["predicted_level"] == "warning"
    assert res["in_boundary"] is False
    assert res["recommended_action"] == "CREATE_WARNING_ALERT"

def test_detector_critical():
    # Outside normal boundaries -> predicted_anomaly = 1, rule says critical
    sensor = {
        "temperature": 45.0,
        "humidity": 15.0,
        "smoke": 400.0,
        "co2": 1000.0,
        "power": 8.0
    }
    res = detect_anomaly(sensor)
    assert res["predicted_anomaly"] == 1
    assert res["predicted_level"] == "critical"
    assert res["in_boundary"] is False
    assert res["recommended_action"] == "CREATE_CRITICAL_ALERT"
