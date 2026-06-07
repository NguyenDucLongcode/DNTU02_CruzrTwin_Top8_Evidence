import os
import sys
import json
import random
import numpy as np
from pathlib import Path
from sklearn.ensemble import IsolationForest
import joblib

# Add project root to path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from src.ai.feature_extractor import extract_features
from src.utils.replay_helpers import load_test_file

MODEL_DIR = Path("models")
REPLAY_DIR = Path("data/replay_test_set")

def generate_synthetic_normal(count: int = 100) -> list:
    """Generates synthetic normal readings for bootstrap training."""
    data = []
    for _ in range(count):
        data.append({
            "temperature": round(random.uniform(23.5, 26.5), 1),
            "humidity": round(random.uniform(50.0, 58.0), 1),
            "air_quality_or_co2": random.randint(390, 450),
            "smoke_status": 0,
            "energy_consumption": random.randint(330, 370)
        })
    return data

def train():
    print("=" * 60)
    print("TRAINING ANOMALY DETECTION MODEL (ISOLATION FOREST)")
    print("=" * 60)
    
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Load normal dataset from replay files
    train_readings = []
    normal_files = list(REPLAY_DIR.glob("normal_*.json"))
    print(f"Loading {len(normal_files)} normal replay files...")
    
    for f in normal_files:
        content = load_test_file(f)
        if content and "readings" in content:
            for r in content["readings"]:
                # Normalize keys
                normalized_r = {
                    "temperature": r.get("temperature", 0.0),
                    "humidity": r.get("humidity", 0.0),
                    "air_quality_or_co2": r.get("co2") or r.get("air_quality_or_co2", 0),
                    "smoke_status": r.get("smoke_status", 0),
                    "energy_consumption": r.get("energy_consumption", 0)
                }
                train_readings.append(normalized_r)
                
    # 2. Add synthetic normal bootstrap data
    synthetic_normal = generate_synthetic_normal(120)
    train_readings.extend(synthetic_normal)
    
    print(f"Total training readings: {len(train_readings)} ({len(train_readings) - 120} replay, 120 synthetic bootstrap)")
    
    # 3. Feature extraction
    X = []
    for r in train_readings:
        feats = extract_features(r)
        X.append([
            feats["temperature"],
            feats["humidity"],
            feats["air_quality_or_co2"],
            feats["smoke_status"],
            feats["energy_consumption"]
        ])
        
    X_arr = np.array(X)
    
    # 4. Train Isolation Forest
    model = IsolationForest(contamination=0.01, random_state=42)
    model.fit(X_arr)
    
    # 5. Save model artifacts
    model_path = MODEL_DIR / "isolation_forest.joblib"
    schema_path = MODEL_DIR / "feature_schema.json"
    
    joblib.dump(model, model_path)
    
    schema = {
        "features": ["temperature", "humidity", "air_quality_or_co2", "smoke_status", "energy_consumption"],
        "num_features": 5,
        "trained_samples": len(train_readings),
        "model_type": "IsolationForest",
        "contamination": 0.01
    }
    
    with open(schema_path, "w", encoding="utf-8") as sf:
        json.dump(schema, sf, indent=2)
        
    print(f"SUCCESS: Model saved successfully at: {model_path}")
    print(f"SUCCESS: Schema saved successfully at: {schema_path}")
    print("=" * 60)

if __name__ == "__main__":
    train()
