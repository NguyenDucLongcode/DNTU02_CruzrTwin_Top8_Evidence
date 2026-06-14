const http = require('http');

const data = JSON.stringify({
    room: "A101", // Giải quyết sự cố ở A101
    temp: 25.0,
    smoke: 0.0,
    co2: 400,
    level: "INFO",
    message: "Khu vực đã an toàn. Lực lượng cứu hoả đã xử lý xong.",
    event: "SYSTEM_RESTORED",
    action: "RETURN_TO_BASE"
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

console.log("🟢 Đã gửi lệnh Reset trạng thái an toàn (Không đụng vào file gốc)!");
