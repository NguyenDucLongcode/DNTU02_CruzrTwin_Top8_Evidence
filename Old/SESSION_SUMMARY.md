# 🚀 DNTU X-Ray | Cruzr Digital Twin - Session Summary
**Thời gian:** 15/06/2026

## 🎯 Mục tiêu đã hoàn thành
Phiên làm việc này tập trung vào việc biến **Static Dashboard** (giao diện tĩnh đọc từ file) thành một hệ thống **Real-time Data-driven Digital Twin** (Mô hình bản sao số hướng dữ liệu thời gian thực) sử dụng Node.js, MongoDB và WebGL (Three.js).

## 🏗️ Kiến trúc Hệ thống (Architecture)
Hệ thống hiện tại vận hành hoàn toàn trên Docker với kiến trúc chuẩn IoT:
1. **Database (`mongo`)**: Cơ sở dữ liệu trung tâm (`cruzrtwin_logs`), chứa các collections: `sensors`, `robot`, `alerts`, `ai`, `state`.
2. **Backend Server (`dashboard-web` - Node.js)**: 
   - Đọc dữ liệu lịch sử từ file `logs/*.jsonl` và tự động bơm (seed) vào MongoDB ở lần chạy đầu tiên.
   - Cung cấp API (`/api/db/sensors`, `/api/logs/:type`) để truy vấn dữ liệu trực tiếp từ MongoDB.
   - Cung cấp HTTP POST API (`/api/simulate`) để giả lập dữ kiện thời gian thực (ghi trực tiếp vào RAM/DB, không ghi đè file text).
3. **Frontend Dashboard (`dashboard.html` - Three.js/Canvas)**:
   - Tự động gọi (polling) API mỗi 2 giây để đồng bộ trạng thái.
   - Hiển thị song song Mô hình toà nhà 3D (phần trên 67% màn hình) và Bản đồ 2D (phần dưới 33% màn hình).

## 🛠️ Các tính năng đã xây dựng
1. **Interactive 3D Model**:
   - Nạp các mô hình `FloorType*.glb` thành toà nhà 5 tầng hoàn chỉnh.
   - Hỗ trợ Raycaster nhấp chuột vào từng phòng để Drill-down xem chi tiết tầng.
   - Khi hover chuột (mousemove) vào bất kỳ phòng/hành lang nào sẽ hiển thị Tooltip thông tin chi tiết (ID, Loại, Tầng).
   - Tự động đổi màu lưới (mesh) các phòng dựa trên dữ liệu cảm biến nhận được từ API (Ví dụ: Cháy -> Đỏ nháy).
2. **Bản đồ 2D thời gian thực**:
   - Được vẽ bằng Canvas (`render2DMap`).
   - Tự động đồng bộ màu cảnh báo cháy nổ khớp 100% với mô hình 3D.
   - Đặc biệt: Có một **Chấm Robot 2D màu xanh lướt đi siêu mượt (60fps Lerp)** hiển thị vị trí của Robot Cruzr khi làm nhiệm vụ.
3. **Quản lý Dữ liệu Thực tế (No Mock Data)**:
   - Xoá bỏ hoàn toàn dữ liệu giả (mock data). Nếu DB không có dữ liệu, mô hình sẽ không tự động báo cháy.

## 📝 Script Kịch bản giả lập
Để test hệ thống, bạn có thể chạy kịch bản mô phỏng báo cháy ở phòng A101 thông qua lệnh:
```bash
node scripts/sim_1_fire_a101.js
```
Kịch bản này sẽ POST một loạt API lên Server Node.js (cách nhau vài giây). Lập tức cả 5 bảng Log trên Web, Mô hình 3D, và Bản đồ 2D sẽ đồng loạt phản ứng (nhấp nháy, đổi màu, robot di chuyển).

## ⚠️ Lưu ý cho Phiên làm việc sau
- **Port Server**: Node.js chạy ở cổng `8000`. Cấu hình listen đã được fix thành `0.0.0.0` để Docker ánh xạ ra ngoài `localhost:8000` thành công.
- **Nếu bị trắng Data**: Kiểm tra xem container `dashboard-web` và `mongo` có đang chạy hay không (`docker compose ps`).
- **Mã nguồn Frontend**: Không được có lỗi Cú pháp JS (Syntax Error) ở file `dashboard.html`, nếu không toàn bộ luồng Render 3D sẽ sập.
- **Robot 3D Marker**: Đã bị gỡ bỏ để nhường chỗ cho Chấm 2D cho bớt rối mắt.

*Bạn có thể Copy nội dung file này cung cấp cho AI ở đầu phiên Chat mới để lấy lại hoàn toàn bối cảnh làm việc.*
