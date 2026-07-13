import os
import json
import joblib
import pandas as pd
from datetime import datetime, timezone

from src.ai.feature_extractor import extract_one
from src.ai.rule_engine import classify_alert_level, DEFAULT_BASELINE
from src.ai.schemas import normalize_sensor_dict
from src.common import config
from src.common.errors import InferenceError
from src.common.time_utils import now_iso

_model_cache = None
_profile_cache = None

def reset_profile_cache():
    """Reset the profile cache, used for testing changes in profile."""
    global _profile_cache
    _profile_cache = None

def load_detector_model(model_path: str):
    """
    Load the IsolationForest model from disk.
    Caches the model to avoid reading it on every call.
    """
    global _model_cache
    if _model_cache is not None:
        return _model_cache
        
    if not os.path.exists(model_path):
        raise InferenceError(f"Model file not found at {model_path}. Train the model first.")
        
    try:
        _model_cache = joblib.load(model_path)
        return _model_cache
    except Exception as e:
        raise InferenceError(f"Failed to load IsolationForest model: {e}")

def load_sensor_profile(profile_path: str) -> dict:
    """
    Load the sensor baseline profile from disk.
    Caches the profile to avoid reading it on every call.
    """
    global _profile_cache
    if _profile_cache is not None:
        return _profile_cache
        
    if not os.path.exists(profile_path):
        return None
        
    try:
        with open(profile_path, "r", encoding="utf-8") as f:
            _profile_cache = json.load(f)
        return _profile_cache
    except Exception as e:
        print(f"Warning: Failed to load sensor profile at {profile_path}: {e}")
        return None

def detect_anomaly(sensor: dict) -> dict:
    """
    Run AI anomaly detection and severity rule checking on sensor input.
    """
    cfg = config.get_config()
    model_path = cfg["model_path"]
    profile_path = cfg.get("sensor_profile_path", "models/sensor_profile.json")
    
    # Normalize keys for backward compatibility
    normalized = normalize_sensor_dict(sensor)
    
    # 1. Load model & profile
    model = load_detector_model(model_path)
    profile = load_sensor_profile(profile_path)
    
    # Determine the baseline configuration
    baseline = None
    baseline_type = "default hardcoded"
    ts = normalized.get("timestamp")
    
    if profile is not None:
        hour_str = None
        day_type_str = None
        if ts:
            try:
                # Accept ISO formats
                cleaned_ts = ts.replace("Z", "+00:00") if isinstance(ts, str) else ts
                dt = pd.to_datetime(cleaned_ts)
                hour_str = str(dt.hour)
                day_type_str = "weekend" if dt.weekday() >= 5 else "working_day"
            except Exception as e:
                print(f"Warning: Failed to parse timestamp {ts}: {e}")
                
        if hour_str is not None and "hourly_baseline" in profile and hour_str in profile["hourly_baseline"]:
            hourly = profile["hourly_baseline"][hour_str]
            has_all_fields = all(field in hourly for field in ["temperature", "humidity", "co2", "smoke_status", "energy_consumption"])
            sample_count = hourly.get("temperature", {}).get("sample_count", 0)
            if has_all_fields and sample_count >= 5:
                baseline = hourly
                baseline_type = f"hourly (hour {hour_str})"
                
        if baseline is None and day_type_str is not None and "day_type_baseline" in profile and day_type_str in profile["day_type_baseline"]:
            dt_base = profile["day_type_baseline"][day_type_str]
            has_all_fields = all(field in dt_base for field in ["temperature", "humidity", "co2", "smoke_status", "energy_consumption"])
            sample_count = dt_base.get("temperature", {}).get("sample_count", 0)
            if has_all_fields and sample_count >= 5:
                baseline = dt_base
                baseline_type = f"day-type ({day_type_str})"
                
        if baseline is None and "global_statistics" in profile:
            baseline = profile["global_statistics"]
            baseline_type = "global monthly"

    if baseline is None:
        baseline = DEFAULT_BASELINE
        baseline_type = "default hardcoded"
    else:
        if profile is not None and "safety_guardrails" in profile:
            baseline = dict(baseline)
            baseline["safety_guardrails"] = profile["safety_guardrails"]
    
    # 2. Extract features
    X = extract_one(normalized)
    
    # 3. Predict & Score
    try:
        pred = model.predict(X)[0]
        score = float(model.decision_function(X)[0])
    except Exception as e:
        raise InferenceError(f"Model prediction failed: {e}")
        
    # 4. Map IsolationForest outputs (1 = normal, -1 = anomaly)
    predicted_anomaly = 0 if pred == 1 else 1
    in_boundary = (predicted_anomaly == 0)
    
    # 5. Extract timestamp or create one
    if not ts:
        ts = now_iso()
        
    features_dict = {
        "temperature": float(normalized.get("temperature", 0.0)),
        "humidity": float(normalized.get("humidity", 0.0)),
        "smoke_status": float(normalized.get("smoke_status", 0.0)),
        "co2": float(normalized.get("co2", 0.0)),
        "energy_consumption": float(normalized.get("energy_consumption", 0.0))
    }
    
    # 6. Format output
    if predicted_anomaly == 0:
        return {
            "timestamp": ts,
            "features": features_dict,
            "model": "IsolationForest",
            "training_logic": "normal_only_boundary_learning",
            "anomaly_score": score,
            "predicted_anomaly": 0,
            "in_boundary": True,
            "predicted_level": "normal",
            "rule_hits": [],
            "rationale": "Sensor values remain within normal operating range.",
            "recommended_action": "NO_ACTION",
            "status": "AI_DETECTED"
        }
    else:
        # Check rule layer
        rule_result = classify_alert_level(normalized, baseline, baseline_type)
        lvl = rule_result["level"]
        rec_action = "CREATE_WARNING_ALERT" if lvl == "warning" else "CREATE_CRITICAL_ALERT"
        
        return {
            "timestamp": ts,
            "features": features_dict,
            "model": "IsolationForest",
            "training_logic": "normal_only_boundary_learning",
            "anomaly_score": score,
            "predicted_anomaly": 1,
            "in_boundary": False,
            "predicted_level": lvl,
            "rule_hits": rule_result["rule_hits"],
            "rationale": rule_result["rationale"],
            "recommended_action": rec_action,
            "status": "AI_DETECTED"
        }