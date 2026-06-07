# RobotAction Entity Schema & Lifecycle

This document describes the attributes, bilingual messages, adapters, and lifecycle transitions for the `RobotAction` entity in FIWARE Orion.

## Orion Entity Schema

The `RobotAction` uses **NGSI-v2 typed attributes** for updating the Orion Context Broker.

### Structure Example

```json
{
  "id": "RobotAction:DNTU02_TOP8_RUN_2026_001:critical_001:CRUZR_01",
  "type": "RobotAction",
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
  "robot_id": {
    "type": "Text",
    "value": "CRUZR_01"
  },
  "alert_id": {
    "type": "Text",
    "value": "AlertEvent:DNTU02_TOP8_RUN_2026_001:critical_001"
  },
  "zone_id": {
    "type": "Text",
    "value": "DNTU_ROOM_A101"
  },
  "action_type": {
    "type": "Text",
    "value": "VOICE_DISPLAY_GUIDANCE"
  },
  "navigation_mode": {
    "type": "Text",
    "value": "PREDEFINED_RESPONSE_POINT"
  },
  "target_location": {
    "type": "Text",
    "value": "RESPONSE_POINT_A101"
  },
  "message_en": {
    "type": "Text",
    "value": "Critical indoor-environment anomaly detected in Room A101. Please follow staff guidance and move calmly to the safe waiting area."
  },
  "message_vi": {
    "type": "Text",
    "value": "Phát hiện bất thường nghiêm trọng trong phòng A101. Vui lòng bình tĩnh làm theo hướng dẫn của nhân viên và di chuyển đến khu vực an toàn."
  },
  "status": {
    "type": "Text",
    "value": "PENDING"
  },
  "adapter": {
    "type": "Text",
    "value": "MockCruzrAdapter"
  },
  "created_at": {
    "type": "DateTime",
    "value": "2026-06-07T03:21:46Z"
  },
  "updated_at": {
    "type": "DateTime",
    "value": "2026-06-07T03:22:41Z"
  }
}
```

---

## Bilingual Voice Output

Bilingual messages are mandatory to support localized evacuations:
- **English (`message_en`)**:
  `Critical indoor-environment anomaly detected in Room A101. Please follow staff guidance and move calmly to the safe waiting area.`
- **Vietnamese (`message_vi`)**:
  `Phát hiện bất thường nghiêm trọng trong phòng A101. Vui lòng bình tĩnh làm theo hướng dẫn của nhân viên và di chuyển đến khu vực an toàn.`

---

## Lifecycle State Machine

Robot action statuses:
- `PENDING`: Task registered but not dispatched.
- `SENT_TO_BRIDGE`: Sent to the local bridge HTTP endpoint.
- `IN_PROGRESS`: Bridge acknowledged and robot is executing the guidance task.
- `GUIDANCE_DELIVERED`: Voice/display guidance completed successfully.
- `ACK_WAITING`: Waiting for manual acknowledgment.
- `ACKED`: Guidance task acknowledged by safety officer.
- `ERROR`: Dispatch failed or timed out.

### Valid Transitions
- `PENDING` -> `SENT_TO_BRIDGE`
- `SENT_TO_BRIDGE` -> `IN_PROGRESS`
- `IN_PROGRESS` -> `GUIDANCE_DELIVERED`
- `GUIDANCE_DELIVERED` -> `ACK_WAITING`
- `ACK_WAITING` -> `ACKED`
- `PENDING` -> `ERROR`
- `SENT_TO_BRIDGE` -> `ERROR`
- `IN_PROGRESS` -> `ERROR`
