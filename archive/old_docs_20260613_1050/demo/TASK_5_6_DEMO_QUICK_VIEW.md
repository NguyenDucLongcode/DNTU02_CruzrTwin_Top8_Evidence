# PRESENTATION QUICK-VIEW: AI + Rule Layer & AlertEvent (Tasks 5 & 6)

This quick reference guide is designed for presenters to quickly summarize the system's workflow, demonstrate key evidence snippets, run live commands, and state safety disclaimers.

---

## 1. 5-Line Summary of the Closed Flow
1. **FIWARE Update**: FIWARE Orion Context Broker publishes a sensor update payload to the webhook receiver.
2. **AI Anomaly Detection**: Isolation Forest computes a multivariate `anomaly_score` on the extracted sensors.
3. **Rule Classification**: The rule layer refines the anomaly level to `critical` and generates a dynamic contextual rationale.
4. **Alert Sync**: An active `AlertEvent` is instantly generated, logged, and synchronized to Orion.
5. **Robot Dispatch**: Cruzr Robot receives a pending `RobotAction` for VOICE_DISPLAY_GUIDANCE to guide occupants.

---

## 2. 3 Key Evidence Snippets (Critical Scenario)

### A. AI Detection Log (`logs/ai_detection.jsonl`)
```json
{
  "demo_run_id": "DNTU02_TOP8_RUN_2026_001",
  "timestamp": "2026-06-13T02:03:28Z",
  "scenario_id": "SCN_CRITICAL_001",
  "zone_id": "DNTU_ROOM_A101",
  "source": "FIWARE_ORION",
  "model": "rule_assisted_isolation_forest",
  "sensor_values": {
    "temperature": 45.0,
    "humidity": 15.0,
    "air_quality_or_co2": 1000.0,
    "smoke_status": 1,
    "energy_consumption": 920.0,
    "raw_smoke_value": 400.0
  },
  "anomaly_score": -0.10393256833379028,
  "predicted_level": "critical",
  "expected_label": "critical",
  "rationale": "High temperature, abnormal air quality, smoke status, and high energy consumption indicate a critical indoor-environment anomaly.",
  "action_code": "DISPATCH_CRUZR_GUIDANCE",
  "recommended_action": "Create critical AlertEvent, send Cruzr to response point, and request operator acknowledgement. Safety-critical actuation should remain operator-approved or simulated.",
  "source_ai_event_id": "AIEvent:SCN_CRITICAL_001"
}
```

### B. AlertEvent SUCCESS Log (`logs/alert_events.jsonl`)
```json
{
  "demo_run_id": "DNTU02_TOP8_RUN_2026_001",
  "timestamp": "2026-06-13T02:03:28Z",
  "alert_id": "AlertEvent:SCN_CRITICAL_001",
  "scenario_id": "SCN_CRITICAL_001",
  "zone_id": "DNTU_ROOM_A101",
  "level": "critical",
  "severity": "critical",
  "status": "ACTIVE",
  "source_model": "rule_assisted_isolation_forest",
  "anomaly_score": -0.10393256833379028,
  "message": "Critical indoor-environment anomaly detected.",
  "action_code": "DISPATCH_CRUZR_GUIDANCE",
  "recommended_action": "Send Cruzr to response point and request operator acknowledgement. Safety-critical actuation should remain operator-approved or simulated.",
  "orion_upsert_status": "SUCCESS",
  "source_ai_event_id": "AIEvent:SCN_CRITICAL_001"
}
```

### C. RobotAction SUCCESS Log (`logs/robot_actions.jsonl`)
```json
{
  "demo_run_id": "DNTU02_TOP8_RUN_2026_001",
  "timestamp": "2026-06-13T02:03:28Z",
  "robot_action_id": "RobotAction:SCN_CRITICAL_001",
  "alert_id": "AlertEvent:SCN_CRITICAL_001",
  "scenario_id": "SCN_CRITICAL_001",
  "zone_id": "DNTU_ROOM_A101",
  "robot_id": "CRUZR_01",
  "action_type": "VOICE_DISPLAY_GUIDANCE",
  "navigation_mode": "PREDEFINED_RESPONSE_POINT",
  "message": "Critical indoor-environment anomaly detected in Room A101. Please follow staff guidance and move calmly to the safe waiting area.",
  "status": "PENDING",
  "orion_upsert_status": "SUCCESS"
}
```

---

## 3. 3 Presentation Commands

### A. Run Automated Verification Tests
```powershell
.venv\Scripts\pytest
```

### B. Query AlertEvent Entity on Orion Context Broker
```bash
curl http://localhost:1026/v2/entities/AlertEvent:SCN_CRITICAL_001
```

### C. Query RobotAction Entity on Orion Context Broker
```bash
curl http://localhost:1026/v2/entities/RobotAction:SCN_CRITICAL_001
```

---

## 4. 1 Crucial Safety Line
> [!WARNING]
> **Safety-critical actuation (e.g., automated firefighting, power cut-off) should remain operator-approved or simulated. Cruzr Robot only performs safe orientation guidance (`VOICE_DISPLAY_GUIDANCE`).**
