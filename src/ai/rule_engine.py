from src.ai.schemas import normalize_sensor_dict

DEFAULT_BASELINE = {
    "temperature": {"normal_low": 20.0, "normal_high": 27.0, "warning_low": 15.0, "warning_high": 31.0, "strong_risk_high": 36.0, "critical_low": 10.0, "critical_high": 38.0},
    "humidity": {"normal_low": 40.0, "normal_high": 75.0, "warning_low": 30.0, "warning_high": 80.0, "strong_risk_high": 85.0, "critical_low": 15.0, "critical_high": 90.0},
    "co2": {"normal_low": 350.0, "normal_high": 500.0, "warning_low": 300.0, "warning_high": 600.0, "strong_risk_high": 850.0, "critical_low": 250.0, "critical_high": 900.0},
    "smoke_status": {"normal_low": 0.0, "normal_high": 0.1, "warning_low": 0.0, "warning_high": 0.5, "strong_risk_high": 0.8, "critical_low": 0.0, "critical_high": 1.0},
    "raw_smoke_value": {"normal_low": 0.0, "normal_high": 80.0, "warning_low": 0.0, "warning_high": 100.0, "strong_risk_high": 250.0, "critical_low": 0.0, "critical_high": 300.0},
    "energy_consumption": {"normal_low": 30.0, "normal_high": 80.0, "warning_low": 15.0, "warning_high": 120.0, "strong_risk_low": 10.0, "strong_risk_high": 110.0, "critical_low": 10.0, "critical_high": 110.0}
}

DEFAULT_SAFETY_GUARDRAILS = {
    "temperature": {
        "critical_floor": 37.0,
        "warning_floor": 30.0,
        "strong_risk_floor": 32.0
    },
    "co2": {
        "critical_floor": 900.0,
        "warning_floor": 600.0,
        "strong_risk_floor": 800.0
    },
    "raw_smoke_value": {
        "critical_floor": 250.0,
        "warning_floor": 100.0,
        "strong_risk_floor": 200.0
    },
    "energy_consumption": {
        "strong_risk_floor": 110.0
    }
}


def fmt(val):
    """Format value: strip .0 to match integer expectations in legacy tests."""
    if abs(val - int(val)) < 1e-9:
        return str(int(val))
    return f"{val:.1f}"

def classify_alert_level(sensor: dict, baseline: dict = None, baseline_type: str = "default hardcoded") -> dict:
    """
    Classify the severity level of an anomaly using rule-based logic driven by baseline profiles.
    Returns a dictionary with:
    - level: "warning" or "critical"
    - rule_hits: list of rules that were triggered
    - rationale: Simple English explanation of the severity classification
    """
    normalized = normalize_sensor_dict(sensor)
    
    temp = float(normalized.get("temperature", 0.0))
    smoke_status = float(normalized.get("smoke_status", 0.0))
    raw_smoke_value = float(normalized.get("raw_smoke_value", smoke_status))
    co2 = float(normalized.get("co2", 0.0))
    energy_consumption = float(normalized.get("energy_consumption", 0.0))
    
    if baseline is None:
        baseline = DEFAULT_BASELINE

    # Get thresholds for each sensor
    b_temp = baseline.get("temperature", DEFAULT_BASELINE["temperature"])
    b_co2 = baseline.get("co2", DEFAULT_BASELINE["co2"])
    b_smoke_raw = baseline.get("raw_smoke_value", DEFAULT_BASELINE["raw_smoke_value"])
    b_energy = baseline.get("energy_consumption", DEFAULT_BASELINE["energy_consumption"])

    # Get safety guardrails from baseline if available, fallback to defaults
    guardrails = baseline.get("safety_guardrails", DEFAULT_SAFETY_GUARDRAILS) if isinstance(baseline, dict) else DEFAULT_SAFETY_GUARDRAILS
    if guardrails is None:
        guardrails = DEFAULT_SAFETY_GUARDRAILS
        
    temp_guard = guardrails.get("temperature", DEFAULT_SAFETY_GUARDRAILS["temperature"])
    co2_guard = guardrails.get("co2", DEFAULT_SAFETY_GUARDRAILS["co2"])
    smoke_guard = guardrails.get("raw_smoke_value", DEFAULT_SAFETY_GUARDRAILS["raw_smoke_value"])
    energy_guard = guardrails.get("energy_consumption", DEFAULT_SAFETY_GUARDRAILS["energy_consumption"])

    rule_hits = []
    is_critical = False
    
    # 1. Direct Critical thresholds (with absolute safety bounds)
    t_crit = max(b_temp["critical_high"], temp_guard.get("critical_floor", 37.0))
    if temp >= t_crit:
        rule_hits.append(f"temperature >= {fmt(t_crit)}")
        is_critical = True
        
    s_crit = b_smoke_raw["critical_high"]
    if smoke_status >= 1.0 or raw_smoke_value >= s_crit:
        rule_hits.append(f"smoke >= {fmt(s_crit)}")
        is_critical = True
        
    c_crit = max(b_co2["critical_high"], co2_guard.get("critical_floor", 900.0))
    if co2 >= c_crit:
        rule_hits.append(f"co2 >= {fmt(c_crit)}")
        is_critical = True
        
    # 2. Compound critical rules / Strong risk signs (with safety floor limits)
    w_smoke = max(b_smoke_raw.get("strong_risk_high", b_smoke_raw.get("warning_high")), smoke_guard.get("strong_risk_floor", 200.0))
    w_temp = max(b_temp.get("strong_risk_high", b_temp.get("warning_high")), temp_guard.get("strong_risk_floor", 32.0))
    w_co2 = max(b_co2.get("strong_risk_high", b_co2.get("warning_high")), co2_guard.get("strong_risk_floor", 800.0))
    
    if raw_smoke_value >= w_smoke and temp >= w_temp:
        rule_hits.append(f"smoke high (>={fmt(w_smoke)}) + temperature high (>={fmt(w_temp)})")
        is_critical = True
        
    # High smoke + high CO2
    if raw_smoke_value >= w_smoke and co2 >= w_co2:
        rule_hits.append(f"smoke high (>= {fmt(w_smoke)}) + co2 high (>= {fmt(w_co2)})")
        is_critical = True
        
    # Define strong risk signs (using strong_risk_high bounds)
    strong_risks = []
    if temp >= w_temp:
        strong_risks.append(f"temp >= {fmt(w_temp)}")
    if smoke_status >= 1.0 or raw_smoke_value >= w_smoke:
        strong_risks.append(f"smoke >= {fmt(w_smoke)}")
    if co2 >= w_co2:
        strong_risks.append(f"co2 >= {fmt(w_co2)}")
        
    energy_low_lim = b_energy.get("strong_risk_low", b_energy.get("warning_low"))
    energy_high_lim = max(b_energy.get("strong_risk_high", b_energy.get("warning_high")), energy_guard.get("strong_risk_floor", 110.0))
    if energy_consumption < energy_low_lim or energy_consumption > energy_high_lim:
        strong_risks.append(f"energy extreme (<{fmt(energy_low_lim)} or >{fmt(energy_high_lim)})")
        
    if len(strong_risks) >= 2:
        rule_hits.append(f"two or more strong risk signs ({', '.join(strong_risks)})")
        is_critical = True

    # 3. Check warning rules (only if not critical)
    if not is_critical:
        if b_temp["warning_high"] <= temp < t_crit:
            rule_hits.append(f"{fmt(b_temp['warning_high'])} <= temperature < {fmt(t_crit)}")
        if b_smoke_raw["warning_high"] <= raw_smoke_value < s_crit:
            rule_hits.append(f"{fmt(b_smoke_raw['warning_high'])} <= smoke < {fmt(s_crit)}")
        if b_co2["warning_high"] <= co2 < c_crit:
            rule_hits.append(f"{fmt(b_co2['warning_high'])} <= co2 < {fmt(c_crit)}")
        if (b_energy["warning_low"] <= energy_consumption < b_energy["normal_low"]) or (b_energy["normal_high"] < energy_consumption <= b_energy["warning_high"]):
            rule_hits.append("energy_consumption is a little outside normal range")

    # Determine final level and rationale
    if baseline_type == "default hardcoded":
        if is_critical:
            level = "critical"
            energy_wording = "high energy consumption" if energy_consumption > energy_high_lim else "abnormal energy consumption"
            rationale = f"High temperature, abnormal air quality, smoke status, and {energy_wording} indicate a critical indoor-environment anomaly."
        else:
            level = "warning"
            rationale = "Abnormal air quality or temperature variation indicates an early warning indoor-environment anomaly."
    else:
        # Build dynamic rationale referring to learned profile
        reasons = []
        if temp >= b_temp.get("normal_high", b_temp.get("warning_high")):
            if "hourly" in baseline_type:
                reasons.append("Temperature is above the learned p95 baseline for this hour.")
            elif "working_day" in baseline_type:
                reasons.append("Temperature is above the learned baseline for working-day afternoon.")
            elif "weekend" in baseline_type:
                reasons.append("Temperature is above the learned baseline for weekend.")
            else:
                reasons.append("Temperature is above the learned monthly baseline.")
        
        if co2 >= b_co2.get("normal_high", b_co2.get("warning_high")):
            if "hourly" in baseline_type:
                reasons.append("CO2 exceeds the learned normal range for this hour.")
            elif "working_day" in baseline_type:
                reasons.append("CO2 exceeds the learned normal range for working-day afternoon.")
            elif "weekend" in baseline_type:
                reasons.append("CO2 exceeds the learned normal range for weekend.")
            else:
                reasons.append("CO2 exceeds the learned monthly baseline.")
                
        if energy_consumption < energy_low_lim or energy_consumption > energy_high_lim:
            if "global" in baseline_type or "monthly" in baseline_type:
                reasons.append("Energy consumption is unusually high compared with the monthly baseline.")
            else:
                reasons.append("Energy consumption is unusually high compared with the learned baseline.")
                
        if smoke_status >= 1.0 or raw_smoke_value >= w_smoke:
            reasons.append("Smoke status indicates abnormal indoor condition.")
            
        if not reasons:
            reasons.append("Sensor values exceed learned normal profile limits.")
            
        if is_critical:
            level = "critical"
            rationale = " ".join(reasons) + " These indicate a critical indoor-environment anomaly."
        else:
            level = "warning"
            rationale = " ".join(reasons) + " These indicate an early warning indoor-environment anomaly."
        
    return {
        "level": level,
        "rule_hits": rule_hits,
        "rationale": rationale
    }
