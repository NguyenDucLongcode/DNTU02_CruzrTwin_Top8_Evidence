# Changelog - Task 5 & Task 6

All changes made to re-implement Task 5 and Task 6 are listed below.

## Files Added

### Common Modules
- `src/common/config.py`
- `src/common/time_utils.py`
- `src/common/logging_utils.py`
- `src/common/json_utils.py`
- `src/common/errors.py`

### AI Modules
- `src/ai/schemas.py`
- `src/ai/data_generator.py`
- `src/ai/data_loader.py`
- `src/ai/feature_extractor.py`
- `src/ai/model_trainer.py`
- `src/ai/rule_engine.py`
- `src/ai/evaluator.py`

### Alert Service
- `src/alerts/alert_schema.py`
- `src/alerts/alert_lifecycle.py`
- `src/alerts/alert_service.py`

### Orchestration
- `src/orchestration/task_5_6_pipeline.py`

### Scripts & Tools
- `scripts/setup/check_environment.py`
- `scripts/ai/generate_sensor_data.py`
- `scripts/ai/train_anomaly_model.py`
- `scripts/ai/evaluate_ai.py`
- `scripts/demo/run_task_5_6_demo.py`
- `scripts/tools/reset_task_5_6_outputs.py`
- `scripts/tools/validate_ai_data.py`
- `scripts/tools/validate_ai_evidence.py`
- `scripts/tools/validate_jsonl_logs.py`
- `scripts/tools/show_task_5_6_trace.py`
- `scripts/tools/assert_task_5_6_acceptance.py`

### Tests
- `tests/unit/test_data_loader.py`
- `tests/unit/test_ai_training_normal_only.py`
- `tests/unit/test_rule_engine.py`
- `tests/unit/test_ai_detector.py`
- `tests/unit/test_alert_service.py`
- `tests/integration/test_closed_loop_task_5_6.py`

## Files Changed

- `requirements.txt`: Updated required python packages.
- `.gitignore`: Added `.env.local`, `*.tmp`, `*.bak`, `*.old`.
- `src/ai/detector.py`: Replaced with new IsolationForest implementation.

## How to Verify

Run the runbook command sequence described in `docs/TASK_5_6_RUNBOOK.md`.
