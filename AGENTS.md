# AGENTS.md — DNTU02 CruzrTwin ASEAN

## Commands

```powershell
# Install
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run all tests (65 total)
env\Scripts\python -m pytest tests/ --tb=short -q

# Run only unit or integration
env\Scripts\python -m pytest tests/unit/ --tb=short -q
env\Scripts\python -m pytest tests/integration/ --tb=short -q

# Demo flow (reset → run → assert)
env\Scripts\python scripts\tools\reset_task_5_6_outputs.py
env\Scripts\python scripts\demo\run_task_5_6_demo.py
env\Scripts\python scripts\tools\assert_task_5_6_acceptance.py

# Training pipeline
env\Scripts\python scripts/data_generation/generate_sensor_data.py --days 30 --interval-minutes 5 --output data/sensor_data.csv
env\Scripts\python scripts/training/build_sensor_profile.py --input data/sensor_data.csv --output models/sensor_profile.json
env\Scripts\python scripts/training/train_anomaly_model.py
env\Scripts\python scripts/training/evaluate_ai.py
```

## Architecture

- **`src/orchestration/pipeline.py`** — Main entrypoint: `process_ai_detector_event` (alias `process_sensor_event` for backward compat)
- **`src/ai/`** — Isolation Forest detector + rule engine
- **`src/alerts/alert_service.py`** — AlertEvent lifecycle, idempotency cache, RobotAction creation
- **`src/robot/cruzr_simulator.py`** — Robot simulator (offline mode: creates default action if none pending)
- **`src/tuya/`** — Tuya Cloud API client (smart plug control, status polling)
- **`src/fiware/`** — FIWARE Orion HTTP client + entity management
- **`docker/tuya-bridge/`** — Docker container to bridge Tuya devices → MQTT (base image: `makuuu2903/tuya-2-mqtt`)

## Key quirks

- **Import path**: Always use `from src.orchestration.pipeline` (NOT `from orchestration.pipeline` — that's the wrong path from before the `src/` restructure)
- **`default_scenario_id`**: Must be present in config (added to `src/common/config.py`)
- **`alert_events.jsonl` logging**: The `append_jsonl` call lives inside `create_alert_event` in `alert_service.py` (was missing, now fixed)
- **`cruzr_simulator.py`**: When no PENDING robot actions exist, it auto-creates a default CRITICAL action in offline mode
- **Tuya config**: `load_tuya_credentials()` reads from `.env` first, falls back to `docker/tuya2mqtt.yaml`
- **`tinytuya>=1.17.2`** required for SG region (`openapi-sg.iotbing.com`)

## Tuya integration

- **Credentials** in `.env`: `TUYA_REGION=sg`, `TUYA_KEY`, `TUYA_SECRET`
- **Device mapping** in `docker/tuya2mqtt.yaml` (YAML: devices list with id, name, device_id, attrs)
- **Bridge** runs as Docker container in `docker/tuya-bridge/` — polls Tuya Cloud every 30s, publishes to MQTT topic `/json/<apikey>/<device_id>/attrs`
- **Local Python client** at `src/tuya/` — `SmartPlugController(device_id)` for direct cloud control
- Untracked files (not yet committed): `src/tuya/`, `docker/tuya-bridge/`, `docker/tuya2mqtt.yaml`

## Testing quirks

- Tests use `tmp_path` fixtures to isolate logs/evidence; no Docker/Orion required
- `reset_alert_service_cache()` must be called between tests to clear idempotency state
- Integration tests train a fresh model on generated data in `tmp_path`
- Mock path for detector: `src.orchestration.pipeline.detect_anomaly`
