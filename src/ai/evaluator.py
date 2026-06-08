import os
import json
import pandas as pd
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score

from src.ai.data_loader import load_sensor_data
from src.ai.detector import detect_anomaly
from src.common import config
from src.common.logging_utils import reset_file, append_jsonl, ensure_dir

def evaluate_model_performance(data_path: str) -> dict:
    """
    Run anomaly detection on the entire dataset, compute metrics, 
    and save logs/evidence.
    """
    cfg = config.get_config()
    
    # Paths
    ai_log_path = os.path.join(cfg["log_dir"], "ai_detection.jsonl")
    matrix_csv_path = os.path.join(cfg["evidence_dir"], "binary_confusion_matrix.csv")
    severity_json_path = os.path.join(cfg["evidence_dir"], "severity_summary.json")
    metrics_json_path = os.path.join(cfg["evidence_dir"], "ai_metrics.json")
    
    # Reset log file
    reset_file(ai_log_path)
    
    # 1. Load data
    df = load_sensor_data(data_path)
    
    y_true = []
    y_pred = []
    
    severity_counts = {
        "normal": 0,
        "warning": 0,
        "critical": 0
    }
    
    # 2. Iterate and detect
    for _, row in df.iterrows():
        sensor = {
            "timestamp": row["timestamp"],
            "temperature": float(row["temperature"]),
            "humidity": float(row["humidity"]),
            "smoke": float(row["smoke"]),
            "co2": float(row["co2"]),
            "power": float(row["power"])
        }
        expected_label = int(row["label"])
        
        # Run detector
        result = detect_anomaly(sensor)
        
        # Log to ai_detection.jsonl (with expected_label)
        log_record = dict(result)
        log_record["expected_label"] = expected_label
        append_jsonl(ai_log_path, log_record)
        
        # Store for metrics
        y_true.append(expected_label)
        y_pred.append(result["predicted_anomaly"])
        
        # Count severity
        severity_counts[result["predicted_level"]] += 1

    # 3. Calculate metrics
    accuracy = float(accuracy_score(y_true, y_pred))
    precision = float(precision_score(y_true, y_pred, pos_label=1, zero_division=0))
    recall = float(recall_score(y_true, y_pred, pos_label=1, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, pos_label=1, zero_division=0))
    
    # Confusion matrix
    # sklearn confusion matrix: tn, fp, fn, tp
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    
    # 4. Save binary confusion matrix CSV
    # Structure: actual,predicted_normal_0,predicted_anomaly_1,total
    ensure_dir(matrix_csv_path)
    matrix_df = pd.DataFrame([
        {
            "actual": "normal_0",
            "predicted_normal_0": int(tn),
            "predicted_anomaly_1": int(fp),
            "total": int(tn + fp)
        },
        {
            "actual": "anomaly_1",
            "predicted_normal_0": int(fn),
            "predicted_anomaly_1": int(tp),
            "total": int(fn + tp)
        }
    ])
    matrix_df.to_csv(matrix_csv_path, index=False)
    
    # 5. Save severity summary JSON
    ensure_dir(severity_json_path)
    with open(severity_json_path, "w", encoding="utf-8") as f:
        json.dump(severity_counts, f, indent=2)
        
    # 6. Save ai metrics JSON
    metrics_summary = {
        "training_logic": "normal_only_boundary_learning",
        "label_meaning": {
            "0": "normal",
            "1": "anomaly"
        },
        "data_path": data_path,
        "accuracy": accuracy,
        "precision_anomaly": precision,
        "recall_anomaly": recall,
        "f1_anomaly": f1,
        "severity_summary": severity_counts,
        "notes": [
            "The model is trained only with label=0 normal data.",
            "Label=1 anomaly data is used only for evaluation."
        ]
    }
    ensure_dir(metrics_json_path)
    with open(metrics_json_path, "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)
        
    return metrics_summary
