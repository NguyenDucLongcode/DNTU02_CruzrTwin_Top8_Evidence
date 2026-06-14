# CLEANUP AUDIT REPORT — DNTU02 CRUZRTWIN ASEAN

Dưới đây là báo cáo rà soát và kế hoạch làm sạch thư mục dự án DNTU02 CruzrTwin ASEAN. Báo cáo tuân thủ nguyên tắc an toàn tuyệt đối, phân loại rõ ràng các loại tệp tin và thư mục trước khi thực hiện dọn dẹp thực tế.

---

## 1. Danh sách phân loại chi tiết (Audit & Classification)

| Đường dẫn File/Folder | Phân loại (Category) | Lý do (Reason) | Đề xuất xử lý (Proposed Action) | Mức độ rủi ro nếu xóa (Risk Level) |
| :--- | :--- | :--- | :--- | :--- |
| **`src/`** | `KEEP_SOURCE` | Thư mục chứa toàn bộ mã nguồn của dự án (AI, alerts, fiware, robot, common). | Giữ nguyên, không thay đổi. | **HIGH** |
| **`tests/`** | `KEEP_TEST` | Thư mục chứa toàn bộ unit test và integration test. | Giữ nguyên, không thay đổi. | **HIGH** |
| **`scripts/`** | `KEEP_REQUIRED` | Thư mục chứa các kịch bản chạy demo, thiết lập hệ thống và scenarios. | Giữ nguyên, không thay đổi. | **HIGH** |
| **`data/`** | `KEEP_REQUIRED` | Thư mục chứa dữ liệu tập tin huấn luyện (`sensor_data.csv`) và dữ liệu test replay. | Giữ nguyên, không thay đổi. | **HIGH** |
| **`docker/`** | `KEEP_CONFIG` | Thư mục chứa cấu hình Docker Compose cho Orion Context Broker và MongoDB. | Giữ nguyên, không thay đổi. | **HIGH** |
| **`models/`** | `KEEP_REQUIRED` | Thư mục lưu trữ model Isolation Forest (`anomaly_model.pkl`) và schema đặc trưng. | Giữ nguyên, không thay đổi. | **HIGH** |
| **`logs/`** | `KEEP_EVIDENCE` | Thư mục chứa các log chạy thật của AI Detection, AlertEvent và RobotAction. | Giữ nguyên các tệp có dữ liệu mới chạy. | **HIGH** |
| **`logs/orion_sync.jsonl`** | `ARCHIVE_OLD_LOG` | Tệp log đồng bộ trống (0 bytes), không chứa dữ liệu quan trọng. | Di chuyển sang thư mục archive. | **LOW** |
| **`evidence/`** | `KEEP_EVIDENCE` | Thư mục chứa các bằng chứng nghiệm thu, ma trận và trace chạy demo. | Giữ nguyên, không thay đổi. | **HIGH** |
| **`docs/`** | `KEEP_REQUIRED` | Thư mục chứa tài liệu đặc tả nghiệp vụ và tài liệu kỹ thuật bản text sạch. | Giữ nguyên, không thay đổi. | **HIGH** |
| **`Công việc demo DNTU02.docx`** | `ARCHIVE_OLD_DOC` | Bản tài liệu Word gốc ở thư mục gốc, đã có bản text tương đương ở `docs/Cong_viec_demo_DNTU02.txt`. | Di chuyển sang thư mục archive. | **LOW** |
| **`Đánh giá DNTU02.docx`** | `ARCHIVE_OLD_DOC` | Bản tài liệu Word đánh giá gốc, đã có bản text tương đương ở `docs/Danh_gia_DNTU02.txt`. | Di chuyển sang thư mục archive. | **LOW** |
| **`CHANGELOG_TASK_5_6.md`** | `KEEP_EVIDENCE` | Nhật ký thay đổi và cập nhật của Task 5 và Task 6. | Giữ nguyên ở root. | **MEDIUM** |
| **`KPI_SCORECARD.md`** | `KEEP_EVIDENCE` | Chỉ số đánh giá hiệu năng KPI của hệ thống. | Giữ nguyên ở root. | **MEDIUM** |
| **`README.md`** | `KEEP_REQUIRED` | Tài liệu hướng dẫn chính của dự án. | Giữ nguyên ở root. | **HIGH** |
| **`TASK_5_6_DEMO_QUICK_VIEW.md`**| `KEEP_EVIDENCE` | Hướng dẫn nhanh cách kiểm chứng demo. | Giữ nguyên ở root. | **HIGH** |
| **`TASK_5_6_FINAL_ACCEPTANCE.md`**| `KEEP_EVIDENCE` | Tài liệu nghiệm thu chính thức của Tasks 5–6. | Giữ nguyên ở root. | **HIGH** |
| **`TEST_REPORT.md`** | `KEEP_EVIDENCE` | Báo cáo kết quả kiểm thử chính thức. | Giữ nguyên ở root. | **MEDIUM** |
| **`generate_sensor_data.py`** | `KEEP_REQUIRED` | Script wrapper ở root để gọi sinh dữ liệu. | Giữ nguyên ở root. | **MEDIUM** |
| **`train_anomaly_model.py`** | `KEEP_REQUIRED` | Script wrapper ở root để gọi huấn luyện model. | Giữ nguyên ở root. | **MEDIUM** |
| **`test_custom_input.py`** | `KEEP_TEST` | Script kiểm thử dữ liệu thủ công từ bàn phím. | Giữ nguyên ở root. | **LOW** |
| **`test_latency.py`** | `KEEP_TEST` | Script đo độ trễ suy luận AI. | Giữ nguyên ở root. | **LOW** |
| **`test_model_working.py`** | `KEEP_TEST` | Script chạy nhanh kiểm tra model hoạt động. | Giữ nguyên ở root. | **LOW** |
| **`test_realtime_simulation.py`**| `KEEP_TEST` | Script mô phỏng luồng stream dữ liệu thời gian thực. | Giữ nguyên ở root. | **LOW** |
| **`test_with_csv.py`** | `KEEP_TEST` | Script kiểm thử model với tệp csv đầu vào. | Giữ nguyên ở root. | **LOW** |
| **`run_all_tests.py`** | `KEEP_TEST` | Script hỗ trợ chạy toàn bộ pytest suites tự động. | Giữ nguyên ở root. | **LOW** |
| **`.env`** | `KEEP_CONFIG` | Tệp cấu hình môi trường chạy thực tế của hệ thống. | Giữ nguyên, không thay đổi. | **HIGH** |
| **`.env.example`** | `KEEP_CONFIG` | Tệp cấu hình môi trường mẫu cho người sử dụng khác. | Giữ nguyên, không thay đổi. | **HIGH** |
| **`.gitignore`** | `KEEP_CONFIG` | Danh sách bỏ qua của Git để ngăn chặn tệp rác. | Cập nhật bổ sung quy tắc bỏ qua. | **HIGH** |
| **`requirements.txt`** | `KEEP_CONFIG` | Danh sách thư viện Python cần thiết của dự án. | Giữ nguyên, không thay đổi. | **HIGH** |
| **`__pycache__/`** | `SAFE_DELETE_CACHE`| Thư mục cache bytecode Python sinh ra khi chạy. | Xóa an toàn. | **LOW** |
| **`.pytest_cache/`** | `SAFE_DELETE_CACHE`| Thư mục cache của pytest sinh ra khi chạy test. | Xóa an toàn. | **LOW** |
| **`.venv/`** | `KEEP_CONFIG` | Môi trường ảo Python của dự án. | Giữ nguyên, không thay đổi. | **HIGH** |
| **`.vscode/`** | `KEEP_CONFIG` | Cấu hình cài đặt Visual Studio Code của nhà phát triển. | Giữ nguyên, không thay đổi. | **HIGH** |

---

## 2. Kế hoạch dọn dẹp chi tiết (Proposed Cleanup Actions)

### A. Giữ nguyên (KEEP)
Toàn bộ mã nguồn dự án (`src/`), dữ liệu kiểm thử (`data/`), các scripts chạy demo (`scripts/`), mô hình học máy (`models/`), docker compose (`docker/`), tài liệu kỹ thuật (`docs/`), và các cấu hình chạy chính thức (`.env`, `.env.example`, `requirements.txt`, `.venv`, `.vscode`) sẽ được giữ nguyên 100%.

### B. Lưu trữ (ARCHIVE)
*   **Vị trí lưu trữ**: Tạo thư mục `archive/old_docs_20260613_1025/` và `archive/old_logs_20260613_1025/`.
*   **Tài liệu lưu trữ**: Di chuyển 2 tệp Word trùng lặp (`Công việc demo DNTU02.docx`, `Đánh giá DNTU02.docx`) từ root vào thư mục archive.
*   **Log lưu trữ**: Di chuyển tệp `logs/orion_sync.jsonl` (trống) vào thư mục archive.
*   **Tệp tin lưu trữ giải thích**: Tạo `archive/README_ARCHIVE.md` mô tả các tệp tin này đã được chuyển đi đâu và lý do.

### C. Xóa an toàn (SAFE DELETE)
Xóa bỏ các thư mục cache tạm thời phát sinh trong quá trình chạy thử nghiệm và đóng gói:
*   `__pycache__/`
*   `.pytest_cache/`

### D. Cập nhật .gitignore (GITIGNORE UPDATE)
Đảm bảo tất cả các cache phát sinh từ pytest, mypy, ruff, các tệp log tạm, tệp bak, tmp và env local đều nằm trong danh sách ignore chính thức.

---

## 3. Đánh giá Rủi ro (Risk Assessment)
Mọi tệp tin thuộc nhóm `KEEP` (bao gồm `KEEP_SOURCE`, `KEEP_TEST`, `KEEP_CONFIG`, `KEEP_REQUIRED`, `KEEP_EVIDENCE`) đều được gắn mức rủi ro **HIGH** hoặc **MEDIUM** và **tuyệt đối không được xóa hay di chuyển**.
Các tệp tin được đề xuất di chuyển hoặc xóa chỉ nằm ở mức rủi ro **LOW** vì chúng là cache tự động hoặc tài liệu Word cũ đã có bản text tương đương trong `docs/`. Vì vậy hành động dọn dẹp là **an toàn tuyệt đối**.
