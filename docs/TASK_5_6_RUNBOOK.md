# Task 5 and 6 Runbook

Use these commands to run and test the AI anomaly detection and alert system.

## Command Steps

1. Check environment:
   ```bash
   python scripts/setup/check_environment.py
   ```
2. Generate sensor data:
   ```bash
   python scripts/ai/generate_sensor_data.py
   ```
3. Validate generated data:
   ```bash
   python scripts/tools/validate_ai_data.py
   ```
4. Train the AI model:
   ```bash
   python scripts/ai/train_anomaly_model.py
   ```
5. Evaluate model performance:
   ```bash
   python scripts/ai/evaluate_ai.py
   ```
6. Run the demo:
   ```bash
   python scripts/demo/run_task_5_6_demo.py
   ```
7. Run the test suite:
   ```bash
   pytest tests/integration/test_closed_loop_task_5_6.py
   ```
