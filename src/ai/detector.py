import os
import joblib
import pandas as pd
from datetime import datetime, timezone

from src.ai.feature_extractor import extract_one
from src.ai.rule_engine import classify_alert_level
from src.common import config
from src.common.errors import InferenceError
from src.common.time_utils import now_iso

_model_cache = None

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

def detect_anomaly(sensor: dict) -> dict:
    """
    Run AI anomaly detection and severity rule checking on sensor input.
    """
    cfg = config.get_config()
    model_path = cfg["model_path"]
    
    # 1. Load model
    model = load_detector_model(model_path)
    
    # 2. Extract features
    X = extract_one(sensor)
    
    # 3. Predict & Score
    try:
        pred = model.predict(X)[0]
        score = float(model.decision_function(X)[0])
    except Exception as e:
        raise InferenceError(f"Model prediction failed: {e}")
        
    # 4. Map IsolationForest outputs (1 = normal, -1 = anomaly)
    # prediction == 1 -> predicted_anomaly = 0
    # prediction == -1 -> predicted_anomaly = 1
    predicted_anomaly = 0 if pred == 1 else 1
    in_boundary = (predicted_anomaly == 0)
    
    # 5. Extract timestamp or create one
    ts = sensor.get("timestamp")
    if not ts:
        ts = now_iso()
        
    features_dict = {
        "temperature": float(sensor.get("temperature", 0.0)),
        "humidity": float(sensor.get("humidity", 0.0)),
        "smoke": float(sensor.get("smoke", 0.0)),
        "co2": float(sensor.get("co2", 0.0)),
        "power": float(sensor.get("power", 0.0))
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
            "rationale": "The sensor data is inside the normal boundary.",
            "recommended_action": "NO_ACTION",
            "status": "AI_DETECTED"
        }
    else:
        # Check rule layer
        rule_result = classify_alert_level(sensor)
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