# DNTU02 CruzrTwin ASEAN - Tasks 5-7

This repository contains the core closed-loop anomaly detection, alerting, and robot action orchestration layers for the building twins demo.

---

## 1. Quick Start

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Train AI Model
Train the explainable Isolation Forest model:
```bash
python scripts/ai/train_ai.py
```

### Evaluate Model
Evaluate accuracy against ground-truth replay sequences:
```bash
python scripts/ai/evaluate_ai.py
```

---

## 2. Run Demo Scenarios

Reset all logs and execute normal, warning, and critical scenarios:
```bash
python scripts/tools/reset_demo_logs.py
python scripts/demo/run_task_5_7_demo.py --all
```

---

## 3. Verify Compliance

### Log Validation
Validate structure and required fields in generated JSONL logs:
```bash
python scripts/tools/validate_jsonl_logs.py
```

### Show Critical Scenario Closed-Loop Trace
Display step-by-step trace showing `AI Anomaly Detection -> AlertEvent -> RobotAction`:
```bash
python scripts/tools/show_demo_trace.py --demo-run-id DNTU02_TOP8_RUN_2026_001 --scenario-id critical_001
```

### Run Acceptance Checks
Assert compliance with acceptance criteria:
```bash
python scripts/tools/assert_task_5_7_acceptance.py
```

---

## 4. Run Tests

Run pytest unit and integration tests:
```bash
pytest
```

---

## 5. Documentation

Refer to the `docs/` folder for implementation details:
- `docs/TASK_5_6_7_IMPLEMENTATION.md`: System architecture and components.
- `docs/AI_RULE_LAYER.md`: AI model details and safety thresholds.
- `docs/ALERTEVENT_SCHEMA.md`: Orion schema and state machine of alerts.
- `docs/ROBOTACTION_SCHEMA.md`: Orion schema, bilingual message limits, and state machine of robot actions.
- `docs/TASK_5_7_RUNBOOK.md`: Commands and operations runbook.
- `docs/KNOWN_LIMITATIONS_TASK_5_7.md`: Safety, privacy, and system boundaries.
