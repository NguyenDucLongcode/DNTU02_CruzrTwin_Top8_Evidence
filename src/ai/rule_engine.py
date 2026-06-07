def evaluate_rules(features: dict) -> dict:
    """
    Evaluates rule criteria based on extracted features.
    Returns:
        dict: {
            "rule_level": str ("normal" | "warning" | "critical"),
            "rule_hits": list of str,
            "rule_confidence": float,
            "rationale": str,
            "risk_score": float
        }
    """
    temp = features["temperature"]
    co2 = features["air_quality_or_co2"]
    smoke = features["smoke_status"]
    energy = features["energy_consumption"]
    hum = features["humidity"]
    multi_risk = features["multi_signal_risk_count"]
    
    rule_hits = []
    rule_level = "normal"
    
    # Calculate risk score base
    # smoke has highest risk weight
    risk_score = 0.0
    if smoke == 1:
        risk_score += 0.5
    
    # temp risk contribution
    if temp >= 38:
        risk_score += 0.3
    elif temp >= 32:
        risk_score += 0.15
        
    # co2 risk contribution
    if co2 >= 1200:
        risk_score += 0.3
    elif co2 >= 900:
        risk_score += 0.15
        
    # energy risk contribution
    if energy >= 900:
        risk_score += 0.2
    elif energy >= 500:
        risk_score += 0.1
        
    # cap risk score at 1.0
    risk_score = min(1.0, risk_score)
    
    # Evaluate Critical rules
    is_critical = False
    
    if smoke == 1:
        rule_hits.append("smoke_status = 1")
        is_critical = True
    if temp >= 38:
        rule_hits.append("temperature >= 38")
        is_critical = True
    if co2 >= 1200:
        rule_hits.append("air_quality_or_co2 >= 1200")
        is_critical = True
    if multi_risk >= 2:
        rule_hits.append(f"multi_signal_risk_count >= 2 ({multi_risk} hit)")
        is_critical = True
    if temp >= 32 and co2 >= 900 and energy >= 500:
        rule_hits.append("temperature high + air quality bad + energy high")
        is_critical = True
        
    if is_critical:
        rule_level = "critical"
        rule_confidence = 0.95
        rationale = f"Critical anomaly detected: {', '.join(rule_hits)}. Environment exhibits significant threat levels."
        # ensure critical risk score is high
        risk_score = max(0.75, risk_score)
        return {
            "rule_level": rule_level,
            "rule_hits": rule_hits,
            "rule_confidence": rule_confidence,
            "rationale": rationale,
            "risk_score": round(risk_score, 2)
        }
        
    # Evaluate Warning rules
    is_warning = False
    if 32 <= temp < 38:
        rule_hits.append("32 <= temperature < 38")
        is_warning = True
    if 900 <= co2 < 1200:
        rule_hits.append("900 <= air_quality_or_co2 < 1200")
        is_warning = True
    if hum > 65:
        rule_hits.append("humidity > 65 (humidity elevated)")
        is_warning = True
    if 500 <= energy < 900:
        rule_hits.append("500 <= energy_consumption < 900")
        is_warning = True
        
    if is_warning and smoke == 0:
        rule_level = "warning"
        rule_confidence = 0.80
        rationale = f"Elevated environmental signals: {', '.join(rule_hits)}. Advisable to monitor closely."
        risk_score = max(0.35, risk_score)
        return {
            "rule_level": rule_level,
            "rule_hits": rule_hits,
            "rule_confidence": rule_confidence,
            "rationale": rationale,
            "risk_score": round(risk_score, 2)
        }
        
    # Default Normal
    rule_hits.append("All signals within normal thresholds")
    rule_level = "normal"
    rule_confidence = 0.90
    rationale = f"All parameters are normal. Temp: {temp}°C, Humidity: {hum}%, CO2: {co2}ppm, Energy: {energy}W."
    risk_score = min(0.2, risk_score)
    return {
        "rule_level": rule_level,
        "rule_hits": rule_hits,
        "rule_confidence": rule_confidence,
        "rationale": rationale,
        "risk_score": round(risk_score, 2)
    }
