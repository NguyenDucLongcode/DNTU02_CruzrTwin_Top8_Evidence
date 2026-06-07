# Known Limitations and Safety Boundaries (Tasks 5-7)

This document describes the safety limits, fallback mechanisms, and limitations of the Tasks 5-7 system implementation.

---

## 1. System Limitations

### explainable_rule_assisted_anomaly_layer
- The anomaly model is an explainable rule-assisted Isolation Forest. While the Isolation Forest detects general deviations, safety checks (temperature, smoke, CO2 levels) are ruled by deterministic thresholds. This ensures that safety is never compromised by an ML classification mistake.
- Synthetic normal data is leveraged as bootstrap training data alongside historical telemetry to supplement baseline representation.

### Orion offline client fallback
- If the Orion Context Broker is unreachable or down, the FIWARE client records an `orion_upsert_status: failed` or `skipped` in the logs.
- The pipeline degrades gracefully by leveraging an in-memory `offline_cache` registry. This allows the local building twin state machine to process and log the entire sequence (AI -> Alert -> Robot guidance) offline.

---

## 2. Safety and Actuation Boundaries

### No safety-critical autonomous actuation
- The autonomous robot (`MockCruzrAdapter`) plays guidance vocal voice broadcasts and displays safety instructions.
- The robot does **NOT** autonomously actuate fire suppression, ventilation gates, or locking mechanisms. These safety-critical actuations are locked behind human operator dashboard approval workflows.

### Privacy constraints (No face recognition/PII)
- The system does **NOT** capture, store, or process Personally Identifiable Information (PII).
- Camera feeds (if any) are processed locally on-edge strictly for spatial mapping and crowd obstacle avoidance. Face recognition or tracking of individuals is strictly disabled to respect GDPR and localized privacy policies.
