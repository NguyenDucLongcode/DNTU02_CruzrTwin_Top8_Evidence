import pytest
import pandas as pd
from src.ai.data_loader import validate_sensor_data, split_train_eval
from src.common.errors import ValidationError

def test_data_loader_valid_schema():
    # Valid dataframe
    data = {
        "timestamp": ["2026-06-08T12:00:00Z", "2026-06-08T12:00:10Z"],
        "temperature": [25.0, 35.0],
        "humidity": [50.0, 60.0],
        "smoke": [40.0, 150.0],
        "co2": [400.0, 700.0],
        "power": [50.0, 90.0],
        "label": [0, 1]
    }
    df = pd.DataFrame(data)
    stats = validate_sensor_data(df)
    assert stats["normal_rows"] == 1
    assert stats["anomaly_rows"] == 1
    assert stats["train_rows"] == 1
    assert stats["eval_rows"] == 2

def test_data_loader_missing_column():
    data = {
        "timestamp": ["2026-06-08T12:00:00Z"],
        "temperature": [25.0],
        "humidity": [50.0],
        "smoke": [40.0],
        "co2": [400.0],
        # "power" is missing
        "label": [0]
    }
    df = pd.DataFrame(data)
    with pytest.raises(ValidationError) as exc:
        validate_sensor_data(df)
    assert "missing" in str(exc.value).lower()

def test_data_loader_invalid_label():
    data = {
        "timestamp": ["2026-06-08T12:00:00Z", "2026-06-08T12:00:10Z"],
        "temperature": [25.0, 30.0],
        "humidity": [50.0, 60.0],
        "smoke": [40.0, 50.0],
        "co2": [400.0, 450.0],
        "power": [50.0, 60.0],
        "label": [0, 2] # 2 is invalid
    }
    df = pd.DataFrame(data)
    with pytest.raises(ValidationError) as exc:
        validate_sensor_data(df)
    assert "label" in str(exc.value).lower()

def test_data_loader_pii_leak():
    data = {
        "timestamp": ["2026-06-08T12:00:00Z", "2026-06-08T12:00:10Z"],
        "temperature": [25.0, 30.0],
        "humidity": [50.0, 60.0],
        "smoke": [40.0, 50.0],
        "co2": [400.0, 450.0],
        "power": [50.0, 60.0],
        "label": [0, 1],
        "face_id": ["face123", "face456"] # PII
    }
    df = pd.DataFrame(data)
    with pytest.raises(ValidationError) as exc:
        validate_sensor_data(df)
    assert "pii" in str(exc.value).lower()

def test_split_train_eval():
    data = {
        "timestamp": ["2026-06-08T12:00:00Z", "2026-06-08T12:00:10Z", "2026-06-08T12:00:20Z"],
        "temperature": [25.0, 30.0, 45.0],
        "humidity": [50.0, 60.0, 15.0],
        "smoke": [40.0, 50.0, 400.0],
        "co2": [400.0, 450.0, 1000.0],
        "power": [50.0, 60.0, 8.0],
        "label": [0, 0, 1]
    }
    df = pd.DataFrame(data)
    train_df, eval_df = split_train_eval(df)
    
    assert len(train_df) == 2
    assert (train_df["label"] == 0).all() # ONLY normal data
    assert len(eval_df) == 3 # ALL data
