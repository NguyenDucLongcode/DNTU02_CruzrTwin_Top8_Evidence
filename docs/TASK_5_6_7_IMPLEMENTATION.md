# Closed-Loop System Architecture & Implementation

This document describes the implementation of the closed-loop anomaly detection, alerting, and robot response system (Tasks 5-7) in the DNTU02 CruzrTwin ASEAN project.

## Architecture Overview

The closed-loop architecture follows a clean, decoupled data pipeline:
```
IoT / Replay Telemetry
  ---> Orion Context Broker (Room State)
  ---> Webhook Receiver (Normalization)
  ---> Event Pipeline Coordinator
  ---> AI + Rule Detection Layer
  ---> AlertEvent Service (Idempotent Alerts)
  ---> RobotAction Service (Guidance Dispatch)
  ---> Mock or Local Bridge Robot Adapter
```

### Components

1. **AI Anomaly Detection & Rule Engine (Task 5)**
   - Combined Isolation Forest model (trained on normal telemetry data) and an explainable rule-based engine.
   - Outputs anomaly score, risk score, rule hits, and a bilingual recommended action.
   - Classification levels: `normal` -> `warning` -> `critical`.

2. **AlertEvent Service (Task 6)**
   - Formulates and manages the lifecycle of alerts.
   - Triggered when AI predicted level is `warning` or `critical`.
   - Normal state does not generate alerts.
   - Prevents duplicate alerts via an Orion idempotency check.
   - Lifecycle: `OPEN` -> `DISPATCHED` -> `ACKED` -> `RESOLVED` -> `ERROR`.

3. **RobotAction Service (Task 7)**
   - Coordinates autonomous robot movements and broadcasting tasks.
   - Dispatches a robot only when alert level is `critical`.
   - Generates bilingual voice/display messages for the robot screen.
   - Transitions: `PENDING` -> `SENT_TO_BRIDGE` -> `IN_PROGRESS` -> `GUIDANCE_DELIVERED`.

---

## File Structure

```
src/
  ├── common/               # Core configurations and utilities
  ├── ai/                   # AI schemas, feature extractor, and rule engine
  ├── alerts/               # AlertEvent schema, service, and lifecycle
  ├── robot/                # RobotAction schema, lifecycle, and adapters
  ├── orchestration/        # Pipeline coordinator and context
  ├── fiware/               # Orion client and webhook receiver
scripts/
  ├── ai/                   # Train and evaluate scripts
  ├── demo/                 # Replay scenario runner
  ├── tools/                # Reset, validation, trace, and assertion tools
tests/
  ├── unit/                 # Components unit tests
  ├── integration/          # Closed-loop pipeline integration tests
docs/                       # System documentation and schemas
```

---

## Verification & Audit Trails

To maintain evidence integrity, the system outputs audit logs in standard JSON Lines (JSONL) format:
- `logs/ai_detection.jsonl`
- `logs/alert_events.jsonl`
- `logs/robot_action.jsonl`

A consolidated summary and critical trace sample are also stored under the `evidence/` directory.
