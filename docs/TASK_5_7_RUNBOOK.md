# Tasks 5-7 System Operations Runbook

This document describes how to execute, verify, test, and troubleshoot Tasks 5-7 (AI Layer, Alerts, and Robot Dispatch).

---

## 1. Initial Setup

1. Configure environment variables in `.env` (copied from `.env.example`).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Train the Isolation Forest model:
   ```bash
   python scripts/ai/train_ai.py
   ```

---

## 2. Model Evaluation

To evaluate model accuracy and log classification performance:
```bash
python scripts/ai/evaluate_ai.py
```
This generates:
- `evidence/ai_metrics.json`
- `evidence/confusion_matrix.csv`
- `logs/ai_detection.jsonl`

---

## 3. Running Demo Scenarios

Clear existing logs and run normal, warning, and critical closed-loop sequences:
```bash
# Reset logs
python scripts/tools/reset_demo_logs.py

# Run all scenarios
python scripts/demo/run_task_5_7_demo.py --all
```

Expectations:
1. **Normal scenario**: AI detects `normal`. AlertEvent and RobotAction are skipped.
2. **Warning scenario**: AI detects `warning`. AlertEvent is created (`status: OPEN`), RobotAction is skipped.
3. **Critical scenario**: AI detects `critical`. AlertEvent is created (`status: OPEN`), RobotAction is created (`status: PENDING`), dispatched via the adapter (`status: GUIDANCE_DELIVERED`), and AlertEvent transitions to `status: DISPATCHED`.

---

## 4. Auditing Logs & Traces

### Validating Schemas
Run the log validator to check if AI, Alert, and Robot JSONL logs comply with system requirements:
```bash
python scripts/tools/validate_jsonl_logs.py
```

### Visualizing Closed-Loop Execution Traces
To trace a specific execution flow (e.g. `critical_001` in run `DNTU02_TOP8_RUN_2026_001`):
```bash
python scripts/tools/show_demo_trace.py --demo-run-id DNTU02_TOP8_RUN_2026_001 --scenario-id critical_001
```

### Asserting Acceptance Compliance
Validate system-wide criteria matches acceptance limits:
```bash
python scripts/tools/assert_task_5_7_acceptance.py
```

---

## 5. Automated Tests

Execute all offline tests:
```bash
pytest
```
- Unit tests cover model schemas, rule conditions, alert states, and robot adapter actions.
- Integration tests cover the entire `Room State` -> `AI` -> `Alert` -> `RobotAction` pipeline.
