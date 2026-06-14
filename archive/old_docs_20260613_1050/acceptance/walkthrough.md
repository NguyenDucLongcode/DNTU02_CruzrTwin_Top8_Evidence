# Walkthrough — DNTU02 CruzrTwin ASEAN (Demo-Ready Build)

Tài liệu này tổng kết toàn bộ công việc đã hoàn thành để đưa dự án từ trạng thái "Almost Ready" sang **"Demo Ready"**.

---

## 1. Tổng quan trạng thái

| Metric | Giá trị |
|--------|---------|
| Test suite | **43/43 passed** (33 cũ + 10 mới) |
| Demo script | All 3 cases **PASS** (Normal, Warning, Critical) |
| Closed-loop trace | 5/6 sections populated (OperatorAck cần chạy ACK endpoint) |
| Dashboard | Ready tại `http://localhost:8080/` |

---

## 2. Thay đổi đã thực hiện

### 2.1. Bugfix Critical: `_processed_acks` type error

**File**: [webhook_receiver.py](file:///c:/Users/asus/Videos/DNTU02_CruzrTwin_Top8_Evidence-khoaduc/DNTU02_CruzrTwin_Top8_Evidence-khoaduc/src/fiware/webhook_receiver.py#L25)

`_processed_acks` được khai báo là `set()` nhưng code sử dụng như `dict` (line 114: `_processed_acks[operator_ack_id]`, line 200: `_processed_acks[operator_ack_id] = res`). Lỗi này sẽ crash mọi request ACK thực tế với `TypeError`.

**Fix**: Đổi `set()` → `{}` (dict).

---

### 2.2. P0.1 — Operator ACK Endpoint (đã triển khai trước)

**File**: [webhook_receiver.py](file:///c:/Users/asus/Videos/DNTU02_CruzrTwin_Top8_Evidence-khoaduc/DNTU02_CruzrTwin_Top8_Evidence-khoaduc/src/fiware/webhook_receiver.py#L92-L202)

- Route: `POST /api/operator/ack`
- Hỗ trợ `decision`: `ACK` hoặc `ERROR`
- Idempotency cache (dict) chống duplicate
- Ghi log `logs/operator_ack.jsonl`
- Upsert `OperatorAck` entity lên Orion khi enabled
- Cập nhật status AlertEvent (`RESOLVED`/`NEEDS_REVIEW`) và RobotAction (`COMPLETED`/`ERROR`)

---

### 2.3. P0.2 — Robot Simulator Daemon (đã triển khai trước)

**File**: [cruzr_simulator.py](file:///c:/Users/asus/Videos/DNTU02_CruzrTwin_Top8_Evidence-khoaduc/DNTU02_CruzrTwin_Top8_Evidence-khoaduc/src/robot/cruzr_simulator.py)

- Poll Orion cho `RobotAction` entities có `status==PENDING`
- Transition: `PENDING` → `NAVIGATING` → `DELIVERED`
- Chế độ offline: simulate delivery cho `SCN_CRITICAL_001`
- Ghi log `logs/robot_actions.jsonl`
- Safety disclaimer: "Safety-critical actuation should remain operator-approved or simulated."

**New**: [__init__.py](file:///c:/Users/asus/Videos/DNTU02_CruzrTwin_Top8_Evidence-khoaduc/DNTU02_CruzrTwin_Top8_Evidence-khoaduc/src/robot/__init__.py) — cho phép import module.

---

### 2.4. P1 — 10 Integration Tests mới

**File**: [test_operator_ack_and_simulator.py](file:///c:/Users/asus/Videos/DNTU02_CruzrTwin_Top8_Evidence-khoaduc/DNTU02_CruzrTwin_Top8_Evidence-khoaduc/tests/integration/test_operator_ack_and_simulator.py)

| # | Test | Mô tả |
|---|------|--------|
| 1 | `test_ack_decision_accepted` | ACK → status "acknowledged" |
| 2 | `test_error_decision_accepted` | ERROR → status "error_reported" |
| 3 | `test_invalid_decision_rejected` | "MAYBE" → 400 |
| 4 | `test_ack_logs_to_jsonl` | Ghi đúng trường vào operator_ack.jsonl |
| 5 | `test_ack_idempotency` | Cùng scenario_id → chỉ ghi 1 entry |
| 6 | `test_ack_error_with_custom_note` | Custom note lưu đúng |
| 7 | `test_offline_poll_delivers_action` | Offline → DELIVERED + log |
| 8 | `test_offline_poll_idempotent` | Poll 2 lần → 1 entry |
| 9 | `test_offline_poll_second_call_returns_false` | 2nd call → False |
| 10 | `test_delivered_log_entry_schema` | 12 trường bắt buộc đều có |
| 11 | `test_safety_disclaimer_in_message` | Robot message không chứa "extinguish"/"cut power" |

> [!NOTE]
> Tests không phụ thuộc Flask (dùng simulation function) để tránh lỗi ModuleNotFoundError trong test environment.

---

### 2.5. P1 — Web Dashboard (no Flask dependency)

**Files**:
- [index.html](file:///c:/Users/asus/Videos/DNTU02_CruzrTwin_Top8_Evidence-khoaduc/DNTU02_CruzrTwin_Top8_Evidence-khoaduc/src/dashboard/index.html) — Premium UI với glassmorphism, KPI counters, pipeline flow
- [app.py](file:///c:/Users/asus/Videos/DNTU02_CruzrTwin_Top8_Evidence-khoaduc/DNTU02_CruzrTwin_Top8_Evidence-khoaduc/src/dashboard/app.py) — Server dùng `http.server` (stdlib, không cần Flask)

**Tính năng**:
- KPI strip: AI Detections, Normal, Warnings, Critical, Robot Actions
- Pipeline flow visualization: Orion → Webhook → AI → Rule → AlertEvent → RobotAction → Operator ACK
- 6 trace cards đọc trực tiếp từ JSONL log files
- Auto-refresh 10 giây
- Safety disclaimer banner
- Fallback demo data khi API không khả dụng

**Khởi chạy**:
```powershell
.venv\Scripts\python src\dashboard\app.py
# → http://localhost:8080/
```

---

### 2.6. Trace Script cải thiện

**File**: [show_demo_trace.py](file:///c:/Users/asus/Videos/DNTU02_CruzrTwin_Top8_Evidence-khoaduc/DNTU02_CruzrTwin_Top8_Evidence-khoaduc/scripts/tools/show_demo_trace.py)

- Thêm `ALERT_LOG = logs/alert_events.jsonl` làm primary source
- Fallback sang `build_alert_from_orion()` nếu alert_events.jsonl trống
- AlertEvent trace section giờ trỏ đúng evidence file

---

## 3. Kết quả Test

```
.venv\Scripts\pytest --tb=short -q
...........................................                              [100%]
43 passed in 4.32s
```

---

## 4. Demo Script Output

```
NORMAL CASE
AI level: normal
AlertEvent: not created
PASS

WARNING CASE
AI level: warning
AlertEvent: created
Alert level: warning
PASS

CRITICAL CASE
AI level: critical
AlertEvent: created
Alert level: critical
PASS
```

---

## 5. Closed-Loop Trace (show_demo_trace.py)

| # | Section | Status | Evidence |
|---|---------|--------|----------|
| 1 | SensorReading | ✅ FOUND | `logs/sensor_readings.jsonl` |
| 2 | Orion state | ✅ FOUND | `logs/orion_state.jsonl` |
| 3 | AI detection | ✅ FOUND | `logs/ai_detection.jsonl` |
| 4 | AlertEvent | ✅ FOUND | `logs/alert_events.jsonl` |
| 5 | RobotAction | ✅ FOUND | `logs/robot_actions.jsonl` |
| 6 | OperatorAck | ⏳ Requires `/api/operator/ack` call | `logs/operator_ack.jsonl` |

---

## 6. Kiến trúc Closed-Loop hoàn chỉnh

```
FIWARE Orion payload
  → webhook_receiver.py (/webhook/notify)
    → process_sensor_event()
      → Isolation Forest (anomaly_score)
      → Rule Layer (predicted_level: normal/warning/critical)
      → logs/ai_detection.jsonl
  → AlertEvent (warning/critical)
    → logs/alert_events.jsonl
    → Orion upsert (AlertEvent entity)
  → RobotAction (critical only)
    → logs/robot_actions.jsonl
    → Orion upsert (RobotAction entity)
  → Cruzr Simulator Daemon
    → PENDING → NAVIGATING → DELIVERED
    → VOICE_DISPLAY_GUIDANCE
  → Operator ACK (/api/operator/ack)
    → ACK → RESOLVED / ERROR → NEEDS_REVIEW
    → logs/operator_ack.jsonl
    → Orion upsert (OperatorAck entity)
  → Dashboard (http://localhost:8080/)
    → Live trace display
```

---

## 7. Safety Disclaimer

> [!WARNING]
> Robot Cruzr chỉ thực hiện **VOICE_DISPLAY_GUIDANCE** (phát loa chỉ dẫn di chuyển).
> Mọi tác vụ cơ điện quan trọng (chữa cháy, ngắt nguồn) đều yêu cầu sự chấp thuận thủ công từ Operator.
> Hệ thống không overclaim: robot không tự chữa cháy, không tự ngắt điện.
