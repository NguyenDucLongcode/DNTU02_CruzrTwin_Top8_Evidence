import os
import sys

# Ensure project root is in path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.ai.model_trainer import train_normal_boundary_model
from src.common.config import get_config

def main():
    config = get_config()
    print("=" * 60)
    print("STARTING MODEL TRAINING...")
    print("=" * 60)
    
    summary = train_normal_boundary_model(
        data_path=config["data_path"],
        model_path=config["model_path"],
        feature_schema_path=config["feature_schema_path"]
    )
    
    print("Model trained and saved successfully.")
    print(f"Model Path: {summary['model_path']}")
    print(f"Feature Schema Path: {summary['feature_schema_path']}")
    print(f"Training normal rows (label=0): {summary['training_rows_label_0_normal']}")
    print(f"Anomaly rows used for training: {summary['anomaly_rows_used_for_training']}")
    print("=" * 60)

if __name__ == "__main__":
    main()
