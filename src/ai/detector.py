import numpy as np
from src.ai.schemas import validate_ai_input
from src.ai.feature_extractor import extract_features
from src.ai.rule_engine import evaluate_rules
from src.ai.model_loader import load_isolation_forest_model
from src.common.time_utils import now_iso

def detect_anomaly(reading: dict) -> dict:
    """
    Validates input schema, extracts features, queries the rule engine,
    and runs the Isolation Forest model if available.
    Returns:
        dict: Complete anomaly detection payload.
    """
    # 1. Schema Validation
    validate_ai_input(reading)
    
    # 2. Extract Features
    features = extract_features(reading)
    
    # 3. Rule Evaluation
    rules_out = evaluate_rules(features)
    rule_level = rules_out["rule_level"]
    rule_hits = rules_out["rule_hits"]
    rule_confidence = rules_out["rule_confidence"]
    rationale = rules_out["rationale"]
    risk_score = rules_out["risk_score"]
    
    # 4. ML Model Evaluation
    model_obj = load_isolation_forest_model()
    if model_obj is not None:
        model_name = "rule_assisted_isolation_forest"
        # Input features for model
        X = [[
            features["temperature"],
            features["humidity"],
            features["air_quality_or_co2"],
            features["smoke_status"],
            features["energy_consumption"]
        ]]
        try:
            # decision_function returns negative values for outliers
            score = float(model_obj.decision_function(X)[0])
            anomaly_score = round(score, 4)
        except Exception:
            # Fallback score mapping based on risk_score
            anomaly_score = round(-0.05 - (risk_score * 0.26), 2)
    else:
        model_name = "explainable_rule_assisted_anomaly_layer"
        # Fallback score mapping
        if rule_level == "critical":
            anomaly_score = -0.31
        elif rule_level == "warning":
            anomaly_score = -0.18
        else:
            anomaly_score = -0.05
            
    # Predicted level prioritizes the safety rule engine
    predicted_level = rule_level
    
    # Recommended Action mapping
    if predicted_level == "critical":
        recommended_action = "CREATE_CRITICAL_ALERT_AND_DISPATCH_CRUZR"
    elif predicted_level == "warning":
        recommended_action = "CREATE_WARNING_ALERT"
    else:
        recommended_action = "NO_ACTION"
        
    return {
        "demo_run_id": reading["demo_run_id"],
        "scenario_id": reading["scenario_id"],
        "scenario_source": reading["scenario_source"],
        "zone_id": reading["zone_id"],
        "timestamp": reading.get("timestamp") or now_iso(),
        "source_entity_id": reading["source_entity_id"],
        "model": model_name,
        "features": features,
        "anomaly_score": anomaly_score,
        "risk_score": risk_score,
        "rule_level": rule_level,
        "rule_hits": rule_hits,
        "rule_confidence": rule_confidence,
        "predicted_level": predicted_level,
        "expected_label": reading.get("expected_label"),
        "rationale": rationale,
        "recommended_action": recommended_action,
        "status": "AI_DETECTED"
    }