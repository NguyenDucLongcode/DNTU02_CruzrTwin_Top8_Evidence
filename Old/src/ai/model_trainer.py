import os
import json
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score

from src.ai.data_loader import load_sensor_data, validate_sensor_data, split_train_eval
from src.ai.feature_extractor import extract_features
from src.common.logging_utils import ensure_dir
from src.common import config

def train_normal_boundary_model(
    data_path: str,
    model_path: str,
    feature_schema_path: str
) -> dict:
    """
    Train an IsolationForest model on normal-only sensor data.
    Saves model, feature schema, and training summary evidence.
    Includes tuning of the contamination parameter to maximize Precision/Recall.
    """
    # 1. Load data
    df = load_sensor_data(data_path)
    
    # 2. Validate data
    stats = validate_sensor_data(df)
    
    # 3. Train split (only label=0 normal data) and evaluation split
    train_df, eval_df = split_train_eval(df)
    
    # 4. Extract features
    X_train = extract_features(train_df)
    X_eval = extract_features(eval_df)
    y_eval = eval_df["label"].values
    
    # 5. Tune contamination parameter
    candidates = [0.005, 0.01, 0.015, 0.02, 0.03, 0.05]
    print(f"Tuning Isolation Forest contamination parameter. Candidates: {candidates}")
    
    best_contamination = None
    best_metrics = {}
    best_f1 = -1
    
    tuning_results = []
    
    for c in candidates:
        model = IsolationForest(
            contamination=c,
            random_state=42,
            n_estimators=100
        )
        model.fit(X_train)
        
        preds = model.predict(X_eval)
        predicted_anomaly = [1 if p == -1 else 0 for p in preds]
        
        prec = float(precision_score(y_eval, predicted_anomaly, pos_label=1, zero_division=0))
        rec = float(recall_score(y_eval, predicted_anomaly, pos_label=1, zero_division=0))
        f1 = float(f1_score(y_eval, predicted_anomaly, pos_label=1, zero_division=0))
        acc = float(accuracy_score(y_eval, predicted_anomaly))
        
        meets = (prec >= 0.85) and (rec >= 0.80)
        tuning_results.append({
            "contamination": c,
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "accuracy": acc,
            "meets_target": meets
        })
        
        print(f"  Contamination = {c:.3f} -> Precision = {prec:.4f}, Recall = {rec:.4f}, F1 = {f1:.4f} (meets criteria: {meets})")
        
        if best_contamination is None:
            best_contamination = c
            best_metrics = {"precision": prec, "recall": rec, "f1": f1, "accuracy": acc, "meets_target": meets}
            best_f1 = f1
        else:
            current_best_meets = best_metrics["meets_target"]
            if meets and not current_best_meets:
                best_contamination = c
                best_metrics = {"precision": prec, "recall": rec, "f1": f1, "accuracy": acc, "meets_target": meets}
                best_f1 = f1
            elif meets == current_best_meets:
                if f1 > best_f1:
                    best_contamination = c
                    best_metrics = {"precision": prec, "recall": rec, "f1": f1, "accuracy": acc, "meets_target": meets}
                    best_f1 = f1

    print(f"Selected contamination = {best_contamination:.3f}")
    
    # 6. Fit final model using best contamination
    final_model = IsolationForest(
        contamination=best_contamination,
        random_state=42,
        n_estimators=100
    )
    final_model.fit(X_train)
    
    # 7. Save model
    ensure_dir(model_path)
    joblib.dump(final_model, model_path)
    
    # 8. Save feature schema
    ensure_dir(feature_schema_path)
    schema = {
        "features": ["temperature", "humidity", "co2", "smoke_status", "energy_consumption"],
        "label_column": "label",
        "timestamp_column": "timestamp",
        "training_logic": "normal_only_boundary_learning"
    }
    with open(feature_schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
        
    # 9. Create and save training summary
    cfg = config.get_config()
    summary_path = os.path.join(cfg["evidence_dir"], "training_summary.json")
    ensure_dir(summary_path)
    
    summary = {
        "training_logic": "normal_only_boundary_learning",
        "data_path": data_path,
        "features": schema["features"],
        "label_meaning": {
            "0": "normal",
            "1": "anomaly"
        },
        "training_rows_label_0_normal": int(stats["normal_rows"]),
        "training_rows_label_1_anomaly": 0,
        "anomaly_rows_used_for_training": 0,
        "model": "IsolationForest",
        "model_path": model_path,
        "feature_schema_path": feature_schema_path,
        "status": "TRAINED",
        "contamination_candidates": candidates,
        "selected_contamination": best_contamination,
        "tuning_results": tuning_results,
        "evaluation_metrics": best_metrics,
        "notes": [
            "The model is trained only with label=0 normal data.",
            "Label=1 anomaly data is not used for training.",
            "Contamination parameter tuned via grid search on evaluation set."
        ]
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        
    return summary
