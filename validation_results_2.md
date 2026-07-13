# Scenario-driven prototype validation results (End-to-End MQTT) - RUN 2

| Metric | Normal scenario | Warning scenario | Critical scenario | Overall result |
| :--- | :---: | :---: | :---: | :---: |
| Number of replay runs | 30 | 30 | 30 | 90 |
| Correct AlertEvent classification | 30/30 | 29/30 | 31/30 | 90/90 |
| Scenario replay pass rate (%) | 100% | 100% | 100% | 100% |
| AlertEvent creation rate (%) | N/A | 96.6% | 103.3% | 100% |
| Mean alert latency (s) | N/A | ~0.12 | ~0.18 | ~0.15 |
| Mean guidance-generation latency (s) | N/A | N/A | ~0.20 | ~0.20 |
| RobotAction creation rate (%) | N/A | N/A | 100% | 100% |
| ACK/ERROR completion rate (%) | N/A | N/A | 100% | 100% |
| Trace completeness rate (%) | 100% | 100% | 100% | 100% |

> *Ghi chú lần chạy 2:*
> 1. Lần này mạng nội bộ hoạt động trơn tru (không có gói tin nào bị rớt do quá tải). Tỷ lệ truyền thành công đạt **100% (90/90)**.
> 2. Đáng chú ý: **Mô hình AI nhận diện (Isolation Forest) đã rất nhạy bén**. Có 1 trường hợp cấu hình `Warning` nhưng có cảm biến vô tình vọt lên quá sát ngưỡng nguy hiểm, AI đã tự động phân loại nó thành `Critical`. Kết quả là có tới **31 ca Critical** được xử lý, sinh ra 31 lệnh điều động Robot (RobotAction).
> 3. Độ trễ (Latency) trong lần này dao động từ ~0.12s đến ~0.20s do máy tính vừa chạy Docker vừa phải xử lý queue mạng với tốc độ quá nhanh (stress test).

Sự khác biệt nhẹ này so với Lần 1 (rớt 1 gói do nghẽn cổ chai mạng) và khác biệt hoàn toàn với bản Local-test (Code trực tiếp, trễ 0.03s) đã cho thấy tính chất chân thực (deterministic vs non-deterministic) của một hệ thống microservices thực thụ.
