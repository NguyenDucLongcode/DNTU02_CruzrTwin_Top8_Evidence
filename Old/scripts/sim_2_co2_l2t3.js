const http = require('http');

const data = JSON.stringify({
    room: "L2-T3",
    temp: 26.5,
    smoke: 5.0,
    co2: 2500,
    level: "CRITICAL",
    message: "Phát hiện Sinh viên ngất xỉu do ngạt khí CO2",
    event: "HVAC_OVERRIDE",
    action: "MEDICAL_ASSIST"
});

const req = http.request('http://localhost:8000/api/simulate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Content-Length': data.length }
}, (res) => {
    res.on('data', d => console.log(d.toString()));
});

req.on('error', error => console.error(error));
req.write(data);
req.end();

console.log("☣️ Đã gửi lệnh thay đổi trạng thái phòng L2-T3 (Không đụng vào file gốc)!");
