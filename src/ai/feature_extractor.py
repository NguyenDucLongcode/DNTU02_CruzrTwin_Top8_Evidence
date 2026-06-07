def extract_features(reading: dict) -> dict:
    """
    Extracts features from the reading dictionary.
    Returns:
        dict: Core and extended features dictionary.
    """
    temp = float(reading.get("temperature", 0.0))
    hum = float(reading.get("humidity", 0.0))
    co2 = int(reading.get("air_quality_or_co2", 0))
    smoke = int(reading.get("smoke_status", 0))
    energy = float(reading.get("energy_consumption", 0.0))
    
    # Delta features can be passed in reading or default to 0.0
    temp_delta = float(reading.get("temperature_delta", 0.0))
    co2_delta = float(reading.get("co2_delta", 0.0))
    energy_delta = float(reading.get("energy_delta", 0.0))
    
    # Risk flags (mapped to critical thresholds to prevent warning scenarios from escalating)
    is_smoke_detected = 1 if smoke == 1 else 0
    is_air_quality_bad = 1 if co2 >= 1100 else 0
    is_temperature_high = 1 if temp >= 35 else 0
    is_energy_abnormal = 1 if energy >= 800 else 0
    
    multi_signal_risk_count = is_smoke_detected + is_air_quality_bad + is_temperature_high + is_energy_abnormal
    
    return {
        "temperature": temp,
        "humidity": hum,
        "air_quality_or_co2": co2,
        "smoke_status": smoke,
        "energy_consumption": energy,
        "temperature_delta": temp_delta,
        "co2_delta": co2_delta,
        "energy_delta": energy_delta,
        "is_smoke_detected": is_smoke_detected,
        "is_air_quality_bad": is_air_quality_bad,
        "is_temperature_high": is_temperature_high,
        "is_energy_abnormal": is_energy_abnormal,
        "multi_signal_risk_count": multi_signal_risk_count
    }
