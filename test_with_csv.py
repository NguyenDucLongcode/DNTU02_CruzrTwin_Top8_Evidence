import os
import pandas as pd
from src.ai.detector import detect_anomaly
from src.common.config import get_config

def main():
    config = get_config()
    csv_path = config["data_path"]
    
    print("=" * 60)
    print(f"EVALUATING MODEL PREDICTIONS ON: {csv_path}")
    print("=" * 60)
    
    if not os.path.exists(csv_path):
        print(f"Data CSV file not found at: {csv_path}")
        return
        
    df = pd.read_csv(csv_path)
    print(f"Dataset Size: {len(df)} rows")
    
    match_count = 0
    anomaly_match = 0
    total_anomalies = (df["label"] == 1).sum()
    total_normals = (df["label"] == 0).sum()
    
    for idx, row in df.iterrows():
        sensor = {
            "temperature": float(row["temperature"]),
            "humidity": float(row["humidity"]),
            "smoke": float(row["smoke"]),
            "co2": float(row["co2"]),
            "power": float(row["power"])
        }
        actual = int(row["label"])
        res = detect_anomaly(sensor)
        pred = res["predicted_anomaly"]
        
        if pred == actual:
            match_count += 1
            if actual == 1:
                anomaly_match += 1
                
    accuracy = (match_count / len(df)) * 100.0
    recall = (anomaly_match / total_anomalies) * 100.0 if total_anomalies > 0 else 100.0
    
    print(f"Model Accuracy: {accuracy:.2f}% ({match_count}/{len(df)})")
    print(f"Anomaly Recall: {recall:.2f}% ({anomaly_match}/{total_anomalies})")
    print(f"Total Normals:  {total_normals}")
    print(f"Total Anomalies:{total_anomalies}")
    print("=" * 60)

if __name__ == "__main__":
    main()
