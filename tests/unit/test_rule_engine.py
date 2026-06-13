import pytest
from src.ai.rule_engine import classify_alert_level

def test_rule_engine_warning():
    # Warning due to elevated temperature (34)
    sensor = {
        "temperature": 34.0,
        "humidity": 65.0,
        "smoke": 80.0,
        "co2": 500.0,
        "power": 50.0
    }
    res = classify_alert_level(sensor)
    assert res["level"] == "warning"
    assert "31 <= temperature < 38" in res["rule_hits"]

def test_rule_engine_critical_temp():
    # Critical due to high temperature (40 >= 38)
    sensor = {
        "temperature": 40.0,
        "humidity": 60.0,
        "smoke": 80.0,
        "co2": 500.0,
        "power": 50.0
    }
    res = classify_alert_level(sensor)
    assert res["level"] == "critical"
    assert "temperature >= 38" in res["rule_hits"]

def test_rule_engine_critical_smoke():
    # Critical due to high smoke (350 >= 300)
    sensor = {
        "temperature": 25.0,
        "humidity": 60.0,
        "smoke": 350.0,
        "co2": 500.0,
        "power": 50.0
    }
    res = classify_alert_level(sensor)
    assert res["level"] == "critical"
    assert "smoke >= 300" in res["rule_hits"]

def test_rule_engine_critical_co2():
    # Critical due to high CO2 (1000 >= 900)
    sensor = {
        "temperature": 25.0,
        "humidity": 60.0,
        "smoke": 50.0,
        "co2": 1000.0,
        "power": 50.0
    }
    res = classify_alert_level(sensor)
    assert res["level"] == "critical"
    assert "co2 >= 900" in res["rule_hits"]

def test_energy_rationale_high_consumption():
    sensor = {
        "temperature": 45.0,
        "humidity": 15.0,
        "smoke": 400.0,
        "co2": 1000.0,
        "power": 920.0
    }
    res = classify_alert_level(sensor)
    assert res["level"] == "critical"
    assert "high energy consumption" in res["rationale"]
    assert "abnormal energy consumption" not in res["rationale"]

def test_energy_rationale_abnormal_low_consumption():
    sensor = {
        "temperature": 45.0,
        "humidity": 15.0,
        "smoke": 400.0,
        "co2": 1000.0,
        "power": 8.0
    }
    res = classify_alert_level(sensor)
    assert res["level"] == "critical"
    assert "abnormal energy consumption" in res["rationale"]
    assert "high energy consumption" not in res["rationale"]

