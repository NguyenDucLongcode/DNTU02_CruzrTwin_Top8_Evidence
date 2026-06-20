import subprocess
import sys

def run_cmd(args):
    print(f"\nRunning command: {' '.join(args)}")
    result = subprocess.run(args, capture_output=False)
    if result.returncode != 0:
        print(f"FAILED: {' '.join(args)}")
        sys.exit(result.returncode)
    print("SUCCESS")

def main():
    print("=" * 60)
    # 1. Environment check
    run_cmd([sys.executable, "scripts/setup/check_environment.py"])
    
    # 2. Reset outputs
    run_cmd([sys.executable, "scripts/tools/reset_task_5_6_outputs.py"])
    
    # 3. Generate sensor data
    run_cmd([sys.executable, "scripts/data_generation/generate_sensor_data.py"])
    
    # 4. Validate data CSV
    run_cmd([sys.executable, "scripts/tools/validate_ai_data.py"])
    
    # 5. Train IsolationForest model
    run_cmd([sys.executable, "scripts/training/train_anomaly_model.py"])
    
    # 6. Evaluate model performance
    run_cmd([sys.executable, "scripts/training/evaluate_ai.py"])
    
    # 7. Run Demo
    run_cmd([sys.executable, "scripts/demo/run_task_5_6_demo.py"])
    
    # 8. Assert Acceptance
    run_cmd([sys.executable, "scripts/tools/assert_task_5_6_acceptance.py"])
    
    # 9. Verify evidence outputs
    run_cmd([sys.executable, "scripts/tools/validate_ai_evidence.py"])
    
    # 10. Verify JSONL logs syntax
    run_cmd([sys.executable, "scripts/tools/validate_jsonl_logs.py"])
    
    # 11. Run pytest unit & integration test suite
    run_cmd([sys.executable, "-m", "pytest", "tests/"])
    
    print("\n" + "=" * 60)
    print("ALL TESTS AND SCRIPTS RAN SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()
