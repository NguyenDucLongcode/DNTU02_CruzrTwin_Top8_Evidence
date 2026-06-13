import os
import sys

# Ensure project root is in path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.ai.evaluator import evaluate_model_performance
from src.common.config import get_config

def main():
    config = get_config()
    print("=" * 60)
    print("STARTING MODEL EVALUATION...")
    print("=" * 60)
    
    metrics = evaluate_model_performance(config["data_path"])
    
    print("Evaluation completed successfully.")
    print(f"Accuracy:  {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision_anomaly']:.4f}")
    print(f"Recall:    {metrics['recall_anomaly']:.4f}")
    print(f"F1 Score:  {metrics['f1_anomaly']:.4f}")
    print("\nSeverity Summary:")
    print(f"  Normal:   {metrics['severity_summary']['normal']}")
    print(f"  Warning:  {metrics['severity_summary']['warning']}")
    print(f"  Critical: {metrics['severity_summary']['critical']}")
    print("=" * 60)

if __name__ == "__main__":
    main()
