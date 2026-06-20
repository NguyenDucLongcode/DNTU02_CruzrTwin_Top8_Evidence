import os
import json
import pandas as pd
import pytest
from datetime import datetime

from src.common.config import get_config
from src.ai.detector import detect_anomaly, load_sensor_profile
from src.ai.rule_engine import classify_alert_level

def test_data_generation_validity():
    csv_path = "data/sensor_data.csv"
    assert os.path.exists(csv_path), "sensor_data.csv does not exist"
    
    df = pd.read_csv(csv_path)
    
    # Check row count
    assert len(df) == 8640, f"Expected 8640 rows, got {len(df)}"
    
    # Check schema
    expected_cols = [
        "timestamp", "zone_id", "temperature", "humidity", "co2",
        "smoke_status", "raw_smoke_value", "energy_consumption",
        "expected_label", "scenario_id"
    ]
    for col in expected_cols:
        assert col in df.columns, f"Column {col} is missing"
    
    assert "power" not in df.columns, "power column should not exist in official CSV"
    assert "label" not in df.columns, "label column should not exist in official CSV"
    
    # Check timestamp uniqueness and continuity
    df["dt"] = pd.to_datetime(df["timestamp"])
    assert df["dt"].is_unique, "Timestamps are not unique"
    
    # Diff of consecutive timestamps should be exactly 5 minutes
    diffs = df["dt"].diff().dropna()
    assert (diffs == pd.Timedelta(minutes=5)).all(), "Timestamps are not continuous at 5-minute intervals"
    
    # Check realistic values
    assert (df["humidity"] >= 0).all() and (df["humidity"] <= 100).all(), "Humidity contains invalid values"
    assert (df["co2"] >= 0).all(), "CO2 has negative values"
    assert (df["energy_consumption"] >= 0).all(), "Energy consumption has negative values"
    assert df["smoke_status"].isin([0, 1]).all(), "smoke_status must be binary 0 or 1"
    
    # Check label distribution
    total = len(df)
    normal_cnt = (df["expected_label"] == "normal").sum()
    warning_cnt = (df["expected_label"] == "warning").sum()
    critical_cnt = (df["expected_label"] == "critical").sum()
    
    normal_pct = normal_cnt / total
    warning_pct = warning_cnt / total
    critical_pct = critical_cnt / total
    
    assert normal_pct > 0.85, f"Normal rows should be majority, got {normal_pct:.2%}"
    assert 0.03 <= warning_pct <= 0.08, f"Warning rows should be around 5-7%, got {warning_pct:.2%}"
    assert 0.005 <= critical_pct <= 0.03, f"Critical rows should be around 1-2%, got {critical_pct:.2%}"

def test_data_cleanup_references():
    # 24h CSV should not be active in the workspace
    assert not os.path.exists("data/sensor_data_24h.csv"), "sensor_data_24h.csv was not cleaned up"
    
    # Config points to sensor_data.csv
    cfg = get_config()
    assert cfg["data_path"] == "data/sensor_data.csv", "Config does not point to sensor_data.csv"
    
    # Check profile metadata source_csv
    profile_path = "models/sensor_profile.json"
    assert os.path.exists(profile_path), "sensor_profile.json does not exist"
    
    with open(profile_path, "r", encoding="utf-8") as f:
        profile = json.load(f)
        
    meta = profile.get("metadata", {})
    assert meta.get("source_csv").replace('\\', '/') == "data/sensor_data.csv", "Profile source_csv is not data/sensor_data.csv"

def test_profile_builder_output():
    profile_path = "models/sensor_profile.json"
    assert os.path.exists(profile_path)
    
    with open(profile_path, "r", encoding="utf-8") as f:
        profile = json.load(f)
        
    # Check top-level elements
    assert "metadata" in profile
    assert "global_statistics" in profile
    assert "hourly_baseline" in profile
    assert "day_type_baseline" in profile
    
    # Check metadata fields
    meta = profile["metadata"]
    fields = [
        "version", "generated_at", "source_csv", "row_count",
        "normal_row_count", "warning_row_count", "critical_row_count",
        "time_coverage_days", "time_coverage_hours",
        "sampling_interval_minutes", "canonical_fields", "label_field"
    ]
    for field in fields:
        assert field in meta, f"Metadata field {field} is missing"
        
    # Check fields present
    assert "energy_consumption" in meta["canonical_fields"]
    assert "power" not in meta["canonical_fields"]
    
    # Check hourly baselines
    for hour in range(24):
        assert str(hour) in profile["hourly_baseline"], f"Hour {hour} is missing in hourly baseline"
        
    # Check day type baselines
    assert "working_day" in profile["day_type_baseline"]
    assert "weekend" in profile["day_type_baseline"]

def test_detector_fallback_behavior():
    profile_path = "models/sensor_profile.json"
    profile = load_sensor_profile(profile_path)
    assert profile is not None
    
    # 1. Weekday hour 14 (should trigger hourly / working_day)
    sensor_weekday = {
        "timestamp": "2026-06-01T14:00:00Z", # June 1, 2026 is Monday (weekday)
        "temperature": 25.0,
        "humidity": 55.0,
        "smoke": 40.0,
        "co2": 400.0,
        "power": 50.0
    }
    res_weekday = detect_anomaly(sensor_weekday)
    assert res_weekday["predicted_level"] == "normal"
    assert "energy_consumption" in res_weekday["features"]
    assert "power" not in res_weekday["features"]
    
    # 2. Weekend hour 14 (should trigger hourly / weekend)
    sensor_weekend = {
        "timestamp": "2026-06-06T14:00:00Z", # June 6, 2026 is Saturday (weekend)
        "temperature": 25.0,
        "humidity": 55.0,
        "smoke": 40.0,
        "co2": 400.0,
        "power": 50.0
    }
    res_weekend = detect_anomaly(sensor_weekend)
    assert "energy_consumption" in res_weekend["features"]
    
    # 3. No timestamp fallback to global
    sensor_no_ts = {
        "temperature": 25.0,
        "humidity": 55.0,
        "smoke": 40.0,
        "co2": 400.0,
        "power": 50.0
    }
    res_no_ts = detect_anomaly(sensor_no_ts)
    assert res_no_ts["predicted_level"] == "normal"
    assert "energy_consumption" in res_no_ts["features"]

def test_detector_is_data_driven(tmp_path):
    from src.ai.detector import reset_profile_cache
    import src.common.config
    
    # Profile A: low thresholds (temperature critical_high = 22.0)
    profile_a = {
        "metadata": {
            "version": "1.1.0",
            "source_csv": "data/sensor_data.csv",
            "canonical_fields": ["temperature", "humidity", "co2", "smoke_status", "energy_consumption"],
            "label_field": "expected_label"
        },
        "global_statistics": {
            "temperature": {"normal_low": 18.0, "normal_high": 21.0, "warning_low": 15.0, "warning_high": 22.0, "strong_risk_high": 22.0, "critical_low": 10.0, "critical_high": 22.0},
            "humidity": {"normal_low": 40.0, "normal_high": 75.0, "warning_low": 30.0, "warning_high": 80.0, "strong_risk_high": 85.0, "critical_low": 15.0, "critical_high": 90.0},
            "co2": {"normal_low": 350.0, "normal_high": 500.0, "warning_low": 300.0, "warning_high": 600.0, "strong_risk_high": 850.0, "critical_low": 250.0, "critical_high": 900.0},
            "smoke_status": {"normal_low": 0.0, "normal_high": 0.1, "warning_low": 0.0, "warning_high": 0.5, "strong_risk_high": 0.8, "critical_low": 0.0, "critical_high": 1.0},
            "raw_smoke_value": {"normal_low": 0.0, "normal_high": 80.0, "warning_low": 0.0, "warning_high": 100.0, "strong_risk_high": 250.0, "critical_low": 0.0, "critical_high": 300.0},
            "energy_consumption": {"normal_low": 30.0, "normal_high": 80.0, "warning_low": 15.0, "warning_high": 120.0, "strong_risk_low": 10.0, "strong_risk_high": 110.0, "critical_low": 10.0, "critical_high": 110.0}
        }
    }
    
    # Profile B: high thresholds (temperature critical_high = 50.0)
    profile_b = {
        "metadata": {
            "version": "1.1.0",
            "source_csv": "data/sensor_data.csv",
            "canonical_fields": ["temperature", "humidity", "co2", "smoke_status", "energy_consumption"],
            "label_field": "expected_label"
        },
        "global_statistics": {
            "temperature": {"normal_low": 18.0, "normal_high": 25.0, "warning_low": 15.0, "warning_high": 45.0, "strong_risk_high": 45.0, "critical_low": 10.0, "critical_high": 50.0},
            "humidity": {"normal_low": 40.0, "normal_high": 75.0, "warning_low": 15.0, "warning_high": 80.0, "strong_risk_high": 85.0, "critical_low": 10.0, "critical_high": 90.0},
            "co2": {"normal_low": 350.0, "normal_high": 500.0, "warning_low": 300.0, "warning_high": 1200.0, "strong_risk_high": 1200.0, "critical_low": 250.0, "critical_high": 1500.0},
            "smoke_status": {"normal_low": 0.0, "normal_high": 0.1, "warning_low": 0.0, "warning_high": 0.5, "strong_risk_high": 0.8, "critical_low": 0.0, "critical_high": 1.0},
            "raw_smoke_value": {"normal_low": 0.0, "normal_high": 80.0, "warning_low": 0.0, "warning_high": 100.0, "strong_risk_high": 250.0, "critical_low": 0.0, "critical_high": 300.0},
            "energy_consumption": {"normal_low": 30.0, "normal_high": 80.0, "warning_low": 15.0, "warning_high": 600.0, "strong_risk_low": 10.0, "strong_risk_high": 600.0, "critical_low": 10.0, "critical_high": 800.0}
        }
    }
    
    path_a = tmp_path / "profile_a.json"
    path_b = tmp_path / "profile_b.json"
    
    with open(path_a, "w") as f:
        json.dump(profile_a, f)
    with open(path_b, "w") as f:
        json.dump(profile_b, f)
        
    sensor_input = {
        "temperature": 42.0,
        "humidity": 18.0,
        "smoke": 40.0,
        "co2": 1000.0,
        "power": 500.0
    }
    
    original_get_config = src.common.config.get_config
    
    # 1. Run with Profile A
    def mock_get_config_a():
        cfg = original_get_config()
        cfg["sensor_profile_path"] = str(path_a)
        return cfg
    src.common.config.get_config = mock_get_config_a
    reset_profile_cache()
    
    res_a = detect_anomaly(sensor_input)
    
    # 2. Run with Profile B
    def mock_get_config_b():
        cfg = original_get_config()
        cfg["sensor_profile_path"] = str(path_b)
        return cfg
    src.common.config.get_config = mock_get_config_b
    reset_profile_cache()
    
    res_b = detect_anomaly(sensor_input)
    
    # Cleanup config mock
    src.common.config.get_config = original_get_config
    reset_profile_cache()
    
    # Asserts
    assert res_a["predicted_anomaly"] == 1
    assert res_b["predicted_anomaly"] == 1
    assert res_a["predicted_level"] == "critical"
    assert res_b["predicted_level"] == "warning"
    assert res_a["recommended_action"] == "CREATE_CRITICAL_ALERT"
    assert res_b["recommended_action"] == "CREATE_WARNING_ALERT"
