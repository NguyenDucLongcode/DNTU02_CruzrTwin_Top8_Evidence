# AlertEvent Entity Schema & Lifecycle

This document describes the attributes and lifecycle requirements for the `AlertEvent` entity in FIWARE Orion.

## Orion Entity Schema

The `AlertEvent` is registered in Orion Context Broker using **NGSI-v2 typed attributes** (no flat dictionaries).

### Structure Example

```json
{
  "id": "AlertEvent:DNTU02_TOP8_RUN_2026_001:critical_001",
  "type": "AlertEvent",
  "demo_run_id": {
    "type": "Text",
    "value": "DNTU02_TOP8_RUN_2026_001"
  },
  "scenario_id": {
    "type": "Text",
    "value": "critical_001"
  },
  "scenario_source": {
    "type": "Text",
    "value": "payload"
  },
  "zone_id": {
    "type": "Text",
    "value": "DNTU_ROOM_A101"
  },
  "source_entity_id": {
    "type": "Text",
    "value": "Room:DNTU_ROOM_A101"
  },
  "level": {
    "type": "Text",
    "value": "critical"
  },
  "status": {
    "type": "Text",
    "value": "OPEN"
  },
  "cause": {
    "type": "StructuredValue",
    "value": {
      "temperature": 37.7,
      "humidity": 74.3,
      "air_quality_or_co2": 1137,
      "smoke_status": 1,
      "energy_consumption": 805
    }
  },
  "ai_result": {
    "type": "StructuredValue",
    "value": {
      "model": "rule_assisted_isolation_forest",
      "anomaly_score": -0.0773,
      "predicted_level": "critical",
      "rationale": "Critical anomaly detected: smoke_status = 1."
    }
  },
  "recommended_action": {
    "type": "Text",
    "value": "DISPATCH_CRUZR_GUIDANCE"
  },
  "created_at": {
    "type": "DateTime",
    "value": "2026-06-07T03:21:40Z"
  },
  "updated_at": {
    "type": "DateTime",
    "value": "2026-06-07T03:22:41Z"
  }
}
```

---

## Lifecycle State Machine

Alert lifecycle statuses:
- `OPEN`: Initial state upon creation.
- `DISPATCHED`: Robot action has been successfully triggered.
- `ACKED`: Operator acknowledged the alert on the dashboard.
- `RESOLVED`: Environment returned to normal and incident closed.
- `ERROR`: Pipeline encountered execution errors (e.g., robot bridge offline).

### Valid State Transitions
- `OPEN` -> `DISPATCHED`
- `DISPATCHED` -> `ACKED`
- `ACKED` -> `RESOLVED`
- `OPEN` -> `ERROR`
- `DISPATCHED` -> `ERROR`

Illegal transitions (e.g., `RESOLVED` -> `OPEN` or `ERROR` -> `DISPATCHED`) are blocked and raise `ValidationError` unless accompanied by a clarifying `recovery_note`.
