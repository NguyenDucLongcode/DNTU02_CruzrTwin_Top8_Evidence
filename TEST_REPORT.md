# Test Report

This document reports the testing results for Task 5 and Task 6.

## Test Objective

We test if the AI model detects anomalies correctly. We test if the rule layer classifies the anomalies into warning and critical levels. We test if alerts are created only when needed.

## Data Logic

- **Normal data** (`label=0`): 1000 rows.
- **Anomaly data** (`label=1`): 200 rows.
- Total rows: 1200 rows.

## Training Logic

- We use the `IsolationForest` model.
- We fit the model using only normal data (`label=0`).
- No anomaly data (`label=1`) is used during training.
- The training feature set excludes `timestamp` and `label`.

## Evaluation Metrics

The actual metrics calculated on the dataset:
- Accuracy: **95.83%** (0.9583)
- Precision (anomaly): **80.00%** (0.8000)
- Recall (anomaly): **100.00%** (1.0000)
- F1 Score (anomaly): **88.89%** (0.8889)

## AlertEvent Result

- **Normal case**: No alert is created.
- **Warning case**: Alert created with level `warning`.
- **Critical case**: Alert created with level `critical`.

## Known Limits

- The data is simulated room telemetry.
- Orion Context Broker is disabled by default for local testing.
