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


def test_rule_engine_dynamic_hourly():
    # Dynamic hourly profile test
    sensor = {
        "temperature": 29.0,
        "humidity": 50.0,
        "smoke": 40.0,
        "co2": 400.0,
        "energy_consumption": 120.0
    }
    custom_baseline = {
        "temperature": {"normal_low": 20.0, "normal_high": 25.0, "warning_low": 18.0, "warning_high": 28.0, "strong_risk_high": 30.0, "critical_low": 15.0, "critical_high": 38.0},
        "co2": {"normal_low": 350.0, "normal_high": 500.0, "warning_low": 300.0, "warning_high": 600.0, "strong_risk_high": 850.0, "critical_low": 250.0, "critical_high": 900.0},
        "raw_smoke_value": {"normal_low": 0.0, "normal_high": 80.0, "warning_low": 0.0, "warning_high": 100.0, "strong_risk_high": 250.0, "critical_low": 0.0, "critical_high": 300.0},
        "energy_consumption": {"normal_low": 30.0, "normal_high": 80.0, "warning_low": 15.0, "warning_high": 110.0, "strong_risk_low": 10.0, "strong_risk_high": 110.0, "critical_low": 10.0, "critical_high": 130.0}
    }
    res = classify_alert_level(sensor, baseline=custom_baseline, baseline_type="hourly (hour 14)")
    assert res["level"] == "warning"
    assert "learned p95 baseline for this hour" in res["rationale"]
    assert "power" not in res["rationale"]
    assert "power" not in "".join(res["rule_hits"])


def test_rule_engine_dynamic_global():
    # Dynamic global profile test with two or more strong risk signs (temp >= 30, energy extreme > 110)
    sensor = {
        "temperature": 32.0,
        "humidity": 50.0,
        "smoke": 40.0,
        "co2": 400.0,
        "energy_consumption": 120.0
    }
    custom_baseline = {
        "temperature": {"normal_low": 20.0, "normal_high": 25.0, "warning_low": 18.0, "warning_high": 28.0, "strong_risk_high": 30.0, "critical_low": 15.0, "critical_high": 38.0},
        "co2": {"normal_low": 350.0, "normal_high": 500.0, "warning_low": 300.0, "warning_high": 600.0, "strong_risk_high": 850.0, "critical_low": 250.0, "critical_high": 900.0},
        "raw_smoke_value": {"normal_low": 0.0, "normal_high": 80.0, "warning_low": 0.0, "warning_high": 100.0, "strong_risk_high": 250.0, "critical_low": 0.0, "critical_high": 300.0},
        "energy_consumption": {"normal_low": 30.0, "normal_high": 80.0, "warning_low": 15.0, "warning_high": 110.0, "strong_risk_low": 10.0, "strong_risk_high": 110.0, "critical_low": 10.0, "critical_high": 130.0}
    }
    res = classify_alert_level(sensor, baseline=custom_baseline, baseline_type="global monthly")
    assert res["level"] == "critical"
    assert "energy extreme" in "".join(res["rule_hits"])
    assert "power" not in "".join(res["rule_hits"])
    assert "monthly baseline" in res["rationale"]


