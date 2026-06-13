def classify_alert_level(sensor: dict) -> dict:
    """
    Classify the severity level of an anomaly using rule-based logic.
    Returns a dictionary with:
    - level: "warning" or "critical"
    - rule_hits: list of rules that were triggered
    - rationale: Simple English explanation of the severity classification
    """
    temp = float(sensor.get("temperature", 0.0))
    smoke = float(sensor.get("smoke", 0.0))
    co2 = float(sensor.get("co2", 0.0))
    power = float(sensor.get("power", 0.0))
    
    rule_hits = []
    is_critical = False
    
    # 1. Direct Critical thresholds
    if temp >= 38.0:
        rule_hits.append("temperature >= 38")
        is_critical = True
    if smoke >= 300.0:
        rule_hits.append("smoke >= 300")
        is_critical = True
    if co2 >= 900.0:
        rule_hits.append("co2 >= 900")
        is_critical = True
        
    # 2. Compound critical rules (using high thresholds to avoid warning cases)
    # High smoke + high temp
    if smoke >= 250.0 and temp >= 36.0:
        rule_hits.append("smoke high (>=250) + temperature high (>=36)")
        is_critical = True
        
    # High smoke + high CO2
    if smoke >= 250.0 and co2 >= 850.0:
        rule_hits.append("smoke high (>=250) + co2 high (>=850)")
        is_critical = True
        
    # Define strong risk signs (close to critical limits)
    strong_risks = []
    if temp >= 36.0:
        strong_risks.append("temp >= 36")
    if smoke >= 250.0:
        strong_risks.append("smoke >= 250")
    if co2 >= 850.0:
        strong_risks.append("co2 >= 850")
    if power < 10.0 or power > 110.0:
        strong_risks.append("power extreme (<10 or >110)")
        
    if len(strong_risks) >= 2:
        rule_hits.append(f"two or more strong risk signs ({', '.join(strong_risks)})")
        is_critical = True

    # 3. Check warning rules (only if not critical)
    if not is_critical:
        if 31.0 <= temp < 38.0:
            rule_hits.append("31 <= temperature < 38")
        if 100.0 <= smoke < 300.0:
            rule_hits.append("100 <= smoke < 300")
        if 600.0 <= co2 < 900.0:
            rule_hits.append("600 <= co2 < 900")
        if (15.0 <= power < 30.0) or (80.0 < power <= 120.0):
            rule_hits.append("power is a little outside normal range")

    # Determine final level
    if is_critical:
        level = "critical"
        energy_wording = "high energy consumption" if power > 110.0 else "abnormal energy consumption"
        rationale = f"High temperature, abnormal air quality, smoke status, and {energy_wording} indicate a critical indoor-environment anomaly."
    else:
        level = "warning"
        rationale = "Abnormal air quality or temperature variation indicates an early warning indoor-environment anomaly."
        
    return {
        "level": level,
        "rule_hits": rule_hits,
        "rationale": rationale
    }
