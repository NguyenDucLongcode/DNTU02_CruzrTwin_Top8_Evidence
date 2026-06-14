# Tài liệu Nghiệm thu: Tích hợp AI + Rule Layer và AlertEvent (Khóa Đặc tả Kỹ thuật)

> [!NOTE]
> This file is no longer a proposed implementation plan. It is the locked implemented behavior summary for Tasks 5 and 6.

Bản tài liệu này tổng kết chính xác trạng thái triển khai thực tế của phần 5 (AI + Rule Layer) và phần 6 (AlertEvent), và luồng nối sang RobotAction tối thiểu.

## User Review Required

> [!IMPORTANT]
> - **Chuẩn hóa smoke_status**:
>   - Trong `sensor_values` của logs/entities, trường `smoke_status` sẽ đại diện cho trạng thái nhị phân: `1` (khi phát hiện khói/smoke >= 1.0) hoặc `0` (bình thường).
>   - Giá trị khói analog gốc sẽ được lưu trữ riêng trong trường `"raw_smoke_value"` (ví dụ: `400.0`) để phục vụ mô hình Isolation Forest mà không làm sai lệch ý nghĩa nhị phân của `smoke_status` theo file đặc tả Word.
> - **Đồng bộ hóa Rationale của energy_consumption**:
>   - Nếu `energy_consumption` lớn hơn 110.0 (tiêu thụ cao), rationale critical sẽ là: `"High temperature, abnormal air quality, smoke status, and high energy consumption indicate a critical indoor-environment anomaly."`.
>   - Nếu `energy_consumption` thấp bất thường (<10.0 hoặc ngoài dải khác nhưng nhỏ hơn 110.0), rationale sẽ đổi thành: `"High temperature, abnormal air quality, smoke status, and abnormal energy consumption indicate a critical indoor-environment anomaly."`.
> - **Các trường hợp Orion Context Broker**:
>   - **Offline mode**: `orion_upsert_status = "SKIPPED_OFFLINE"`
>   - **Live mode thành công**: `orion_upsert_status = "SUCCESS"`
>   - **Live mode lỗi/mất mạng**: `orion_upsert_status = "FAILED"` kèm trường `error_message`.

---

## Implemented & Verified Behavior

### 1. Webhook Receiver — Implemented & Verified

#### [MODIFY] [webhook_receiver.py](file:///c:/Users/asus/Videos/DNTU02_CruzrTwin_Top8_Evidence-khoaduc/DNTU02_CruzrTwin_Top8_Evidence-khoaduc/src/fiware/webhook_receiver.py)
- Webhook cập nhật cảm biến sẽ parse metadata từ Orion payload, gọi `process_sensor_event`.

---

### 2. Orchestration Pipeline — Implemented & Verified

#### [MODIFY] [task_5_6_pipeline.py](file:///c:/Users/asus/Videos/DNTU02_CruzrTwin_Top8_Evidence-khoaduc/DNTU02_CruzrTwin_Top8_Evidence-khoaduc/src/orchestration/task_5_6_pipeline.py)
- Cập nhật `process_sensor_event(orion_payload)`:
  - **Trình tự chạy AI + Rule**: Gọi mô hình Isolation Forest trước để tạo `anomaly_score`. Sau đó, Rule Layer mới phân loại `predicted_level` (normal/warning/critical) dựa trên điểm dị thường và các luật phụ trợ. Rule Layer không thay thế mô hình AI, và hệ thống không được chỉ sử dụng if-else/threshold đơn giản để kết luận sự cố.
  - Lấy 5 sensor fields gốc.
  - Kiểm tra thiếu dữ liệu cảm biến quan trọng.
  - Chuẩn hóa `sensor_values`:
    - `smoke_status` lưu dạng nhị phân: `1` nếu smoke >= 1.0 else `0`.
    - Expose thêm trường `raw_smoke_value` lưu giá trị analog gốc.
  - Ghi AI Detection Log vào `logs/ai_detection.jsonl` đúng cấu trúc schema tối thiểu.
  - Gọi `create_alert_event` nếu warning hoặc critical.

---

### 3. Alert Event Service — Implemented & Verified

#### [MODIFY] [alert_service.py](file:///c:/Users/asus/Videos/DNTU02_CruzrTwin_Top8_Evidence-khoaduc/DNTU02_CruzrTwin_Top8_Evidence-khoaduc/src/alerts/alert_service.py)
- Cập nhật `create_alert_event`:
  - Trả về đối tượng có: `"status": "OPEN"`, `"evidence_status": "ACTIVE"`, `"recommended_action"` là câu mô tả đầy đủ.
  - Ghi log vào `logs/alert_events.jsonl` sử dụng: `"status": "ACTIVE"`, `"recommended_action"` dạng câu mô tả chi tiết, giữ cả trường `level` và `severity` khớp với `predicted_level`.
  - Đồng bộ NGSI-v2 thực thể `AlertEvent` lên Orion.
  - Nếu `critical`, gọi `create_robot_action_from_alert`.

---

### 4. Rule Engine — Implemented & Verified

#### [MODIFY] [rule_engine.py](file:///c:/Users/asus/Videos/DNTU02_CruzrTwin_Top8_Evidence-khoaduc/DNTU02_CruzrTwin_Top8_Evidence-khoaduc/src/ai/rule_engine.py)
- Cập nhật hàm `classify_alert_level`:
  - Tự động thay đổi mô tả tiêu thụ năng lượng trong `rationale` dựa theo giá trị `power`.
  - Sử dụng `"high energy consumption"` khi power > 110.0, ngược lại sử dụng `"abnormal energy consumption"`.

---

### 5. RobotAction Bridge — Implemented & Verified

- Tích hợp gửi RobotAction lên Orion Context Broker khi có sự cố Critical, tự động định dạng `Room <tên_phòng>` sạch và đồng bộ trường `robot_id` trong logs.

---

## Implemented Verification Summary

### Automated Tests — 33/33 Passed
- Thực hiện chạy toàn bộ test suite bằng lệnh:
  ```powershell
  .venv\Scripts\pytest
  ```
- Đảm bảo tất cả 33 tests pass 100%.

### Live Orion Verification — Documented
- Xác minh log trong cả kịch bản offline (`SKIPPED_OFFLINE`), live thành công (`SUCCESS`), và live lỗi kết nối (`FAILED`).
- Sử dụng các lệnh `curl` để truy vấn thực thể trên Orion.

### Safety Limitations — Documented
- Đảm bảo hoạt động quan trọng như ngắt điện hay chữa cháy là simulated hoặc operator-approved. Robot Cruzr chỉ thực hiện phát loa chỉ dẫn di chuyển thoát hiểm (`VOICE_DISPLAY_GUIDANCE`).

### Offline/SUCCESS/FAILED modes — Verified
- Các chế độ hoạt động của Orion Context Broker đã được xác minh thành công và ghi log tương ứng.
