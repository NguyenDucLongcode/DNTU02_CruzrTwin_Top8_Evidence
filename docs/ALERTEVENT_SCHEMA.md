# AlertEvent Schema

An AlertEvent is a JSON structure created when the AI detector finds an anomaly in the room sensor data.

## Rules for Alerts

- **Normal**: No alert is created.
- **Warning**: A warning AlertEvent is created. Status starts as `OPEN`. Recommended action is `CHECK_ROOM`.
- **Critical**: A critical AlertEvent is created. Status starts as `OPEN`. Recommended action is `DISPATCH_CRUZR_GUIDANCE`.

## Alert Fields

- `alert_id`: Unique identifier for the alert (e.g. `AlertEvent:2026-06-08T12:00:10Z`).
- `timestamp`: Time when the anomaly occurred.
- `level`: Severity level (`warning` or `critical`).
- `status`: Lifecycle state (`OPEN`, `ACKED`, `RESOLVED`, or `ERROR`).
- `source`: Source of the alert (`AI_DETECTION`).
- `message`: Description of the alert.
- `recommended_action`: Recommended response action.
- `ai_result`: Reference to the AI prediction result.
