import os
import json
import pytest
import pandas as pd
from src.ai.model_trainer import train_normal_boundary_model

@pytest.fixture(autouse=True)
def patch_config_dir(tmp_path):
    import src.common.config
    original_get_config = src.common.config.get_config
    
    # Create temp evidence dir
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    
    def mock_get_config():
        cfg = original_get_config()
        cfg["evidence_dir"] = str(evidence_dir)
        return cfg
        
    src.common.config.get_config = mock_get_config
    yield
    src.common.config.get_config = original_get_config

def test_training_normal_only(tmp_path):
    # Create a dummy dataset with normal and anomaly rows
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    csv_file = data_dir / "sensor_data.csv"
    
    data = {
        "timestamp": ["2026-06-08T12:00:00Z"] * 20 + ["2026-06-08T12:00:10Z"] * 5,
        "temperature": [25.0] * 20 + [45.0] * 5,
        "humidity": [50.0] * 20 + [15.0] * 5,
        "smoke": [40.0] * 20 + [400.0] * 5,
        "co2": [400.0] * 20 + [1000.0] * 5,
        "power": [50.0] * 20 + [8.0] * 5,
        "label": [0] * 20 + [1] * 5 # 20 normal, 5 anomaly
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_file, index=False)
    
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    model_path = models_dir / "anomaly_model.pkl"
    schema_path = models_dir / "feature_schema.json"
    
    # Run trainer
    summary = train_normal_boundary_model(
        data_path=str(csv_file),
        model_path=str(model_path),
        feature_schema_path=str(schema_path)
    )
    
    # Assertions
    assert summary["training_rows_label_0_normal"] == 20
    assert summary["training_rows_label_1_anomaly"] == 0
    assert summary["anomaly_rows_used_for_training"] == 0
    assert summary["status"] == "TRAINED"
    
    # Check that model file was written
    assert model_path.exists()
    assert schema_path.exists()
