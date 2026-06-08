# DNTU02 CruzrTwin ASEAN - Task 5 & Task 6

This repository contains the implementation of Task 5 (AI Anomaly Detection and Rule Layer) and Task 6 (AlertEvent Management).

## What it does

1. **AI Anomaly Detection**: An Isolation Forest model learns the boundaries of normal sensor readings (using `label=0` data only).
2. **Rule Layer**: When the AI detects an anomaly, a rule-based engine classifies the severity level into `warning` or `critical`.
3. **AlertEvent Service**: Automatically creates alert events for warning and critical detections, tracking their lifecycle status as `OPEN`.

## Quick Start

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Verify environment:
   ```bash
   python scripts/setup/check_environment.py
   ```
3. Generate dataset:
   ```bash
   python scripts/ai/generate_sensor_data.py
   ```
4. Train Isolation Forest:
   ```bash
   python scripts/ai/train_anomaly_model.py
   ```
5. Evaluate model:
   ```bash
   python scripts/ai/evaluate_ai.py
   ```
6. Run interactive demo:
   ```bash
   python scripts/demo/run_task_5_6_demo.py
   ```

## Evidence Files

After running, evidence is generated in the `evidence/` directory:
- `training_summary.json`: Training configuration and bounds parameters.
- `ai_metrics.json`: Accuracy, Precision, Recall, and F1 metrics on the test dataset.
- `binary_confusion_matrix.csv`: Confusion matrix of evaluations.
- `task_5_6_test_summary.json`: Success status of demo scenarios.
- `task_5_6_trace_sample.json`: Detailed event flow trace.
