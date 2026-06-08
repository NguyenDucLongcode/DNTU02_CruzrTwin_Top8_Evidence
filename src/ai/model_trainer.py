import os
import json
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest

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
    """
    # 1. Load data
    df = load_sensor_data(data_path)
    
    # 2. Validate data
    stats = validate_sensor_data(df)
    
    # 3. Train split (only label=0 normal data)
    train_df, _ = split_train_eval(df)
    
    # 4. Extract features
    X_train = extract_features(train_df)
    
    # 5. Train IsolationForest
    model = IsolationForest(
        contamination=0.05,
        random_state=42,
        n_estimators=100
    )
    model.fit(X_train)
    
    # 6. Save model
    ensure_dir(model_path)
    joblib.dump(model, model_path)
    
    # 7. Save feature schema
    ensure_dir(feature_schema_path)
    schema = {
        "features": ["temperature", "humidity", "smoke", "co2", "power"],
        "label_column": "label",
        "timestamp_column": "timestamp",
        "training_logic": "normal_only_boundary_learning"
    }
    with open(feature_schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
        
    # 8. Create and save training summary
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
        "notes": [
            "The model is trained only with label=0 normal data.",
            "Label=1 anomaly data is not used for training."
        ]
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        
    return summary
