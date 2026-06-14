const http = require('http');

function sendSim(data) {
    const req = http.request('http://localhost:8000/api/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(JSON.stringify(data)) }
    }, res => res.on('data', d => {}));
    req.on('error', () => {});
    req.write(JSON.stringify(data));
    req.end();
}

console.log("🎬 BẮT ĐẦU KỊCH BẢN 1: HOẢ HOẠN TẠI A101 (Timeline 12 giây)...");

// T = 0s: Khói nhẹ, nhiệt độ tăng nhẹ
setTimeout(() => {
    console.log("[T=0s] Sensor phát hiện khói nhẹ...");
    sendSim({ room: "A101", temp: 35.5, smoke: 15.0, co2: 600, state_status: "WARNING" });
}, 0);

// T = 3s: AI Camera xác nhận có khói bốc lên
setTimeout(() => {
    console.log("[T=3s] AI phân tích hình ảnh...");
    sendSim({ level: "WARNING", message: "Phát hiện khói tại A101", room: "A101" });
}, 3000);

// T = 6s: Đám cháy bùng phát, cảm biến vọt lên Critical
setTimeout(() => {
    console.log("[T=6s] Lửa bùng phát, Sensor báo động đỏ...");
    sendSim({ room: "A101", temp: 75.5, smoke: 90.0, co2: 1200, state_status: "CRITICAL_FIRE" });
}, 6000);

// T = 9s: Hệ thống Alert tự động kích hoạt
setTimeout(() => {
    console.log("[T=9s] Kích hoạt chuông báo cháy toàn tầng...");
    sendSim({ event: "FIRE_ALARM_TRIGGERED", room: "A101", level: "CRITICAL", message: "Đám cháy lan rộng (Conf: 99%)" });
}, 9000);

// T = 12s: Robot Cruzr nhận lệnh đi kiểm tra
setTimeout(() => {
    console.log("[T=12s] Điều phối Robot Cruzr...");
    sendSim({ action: "EMERGENCY_NAV", room: "A101" });
    console.log("✅ Hoàn tất chuỗi sự kiện! Mời bạn nhìn Dashboard!");
}, 12000);
