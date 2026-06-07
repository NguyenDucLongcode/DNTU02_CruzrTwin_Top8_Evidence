import os
import sys

# Add project root to path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from src.ai.rule_engine import evaluate_rules
from src.ai.feature_extractor import extract_features

def test_normal_reading():
    reading = {
        "temperature": 25.0,
        "humidity": 55.0,
        "air_quality_or_co2": 420,
        "smoke_status": 0,
        "energy_consumption": 350
    }
    feats = extract_features(reading)
    res = evaluate_rules(feats)
    assert res["rule_level"] == "normal"
    assert len(res["rationale"]) > 0
    assert len(res["rule_hits"]) > 0
    assert "normal" in res["rationale"].lower()

def test_warning_temperature():
    reading = {
        "temperature": 34.0,
        "humidity": 55.0,
        "air_quality_or_co2": 420,
        "smoke_status": 0,
        "energy_consumption": 350
    }
    feats = extract_features(reading)
    res = evaluate_rules(feats)
    assert res["rule_level"] == "warning"
    assert any("temperature" in hit for hit in res["rule_hits"])

def test_warning_co2():
    reading = {
        "temperature": 25.0,
        "humidity": 55.0,
        "air_quality_or_co2": 950,
        "smoke_status": 0,
        "energy_consumption": 350
    }
    feats = extract_features(reading)
    res = evaluate_rules(feats)
    assert res["rule_level"] == "warning"
    assert any("co2" in hit or "air_quality" in hit for hit in res["rule_hits"])

def test_smoke_critical():
    reading = {
        "temperature": 25.0,
        "humidity": 55.0,
        "air_quality_or_co2": 420,
        "smoke_status": 1,
        "energy_consumption": 350
    }
    feats = extract_features(reading)
    res = evaluate_rules(feats)
    assert res["rule_level"] == "critical"
    assert any("smoke" in hit for hit in res["rule_hits"])

def test_multiple_risks_critical():
    reading = {
        "temperature": 33.0, # warning temp
        "humidity": 55.0,
        "air_quality_or_co2": 950, # warning co2
        "smoke_status": 0,
        "energy_consumption": 510 # warning energy
    }
    feats = extract_features(reading)
    res = evaluate_rules(feats)
    # 3 warnings -> critical level since multi_signal_risk_count >= 2
    assert res["rule_level"] == "critical"
