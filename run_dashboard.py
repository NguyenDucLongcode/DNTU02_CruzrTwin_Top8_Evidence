import http.server
import socketserver
import json
import random
import time
import os
import sys

# Khai báo cổng
PORT = 8000

# Thử import AI từ nhánh khoaduc (nếu có lỗi import sẽ dùng logic fallback)
try:
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    from src.ai.detector import AnomalyDetector
    ai_detector = AnomalyDetector()
    print("[AI ENGINE] Đã load thành công model từ src/ai")
    HAS_AI = True
except Exception as e:
    print(f"[AI ENGINE WARNING] Không thể load model AI: {e}. Sẽ dùng logic Fallback.")
    HAS_AI = False

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        super().end_headers()

    def do_GET(self):
        # 1. API: Lấy Log hệ thống (AI & Events)
        if self.path == '/api/logs':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            logs = []
            log_path = 'logs/alert_events.jsonl'
            if os.path.exists(log_path):
                with open(log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Lấy 10 dòng log mới nhất
                    for line in lines[-10:]:
                        try:
                            logs.append(json.loads(line.strip()))
                        except:
                            pass
            
            # Thêm 1 log sinh động báo AI đang chạy
            logs.append({
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "alert_id": "SYS_INFO",
                "location": "System",
                "severity": "info",
                "message": "AI Engine is actively monitoring 620 sensors."
            })
            
            self.wfile.write(json.dumps(logs).encode())
            return

        # 2. API: Cấu trúc giả lập FIWARE Orion (Tích hợp AI)
        elif self.path.startswith('/v2/entities'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            # Giả lập dữ liệu cho các phòng (L1-T1 đến L5-B10)
            # Trong thực tế, đoạn này sẽ `requests.get('http://[DOCKER_IP]:1026/v2/entities')`
            entities = []
            
            # Tạo dữ liệu ngẫu nhiên cho một số phòng để Demo
            demo_rooms = ['A101', 'L3-T2', 'L5-B4']
            
            for room in demo_rooms:
                temp = round(random.uniform(22, 28), 1)
                co2 = round(random.uniform(400, 500), 0)
                smoke = 0
                
                # Cố tình tạo dị thường ở A101
                if room == 'A101' and int(time.time()) % 10 < 5: 
                    temp = 48.5
                    co2 = 1200
                    smoke = 1
                
                # --- GỌI LÕI AI ĐỂ PHÂN TÍCH (TỪ KHOA ĐỨC) ---
                if HAS_AI and room == 'A101':
                    # Đưa data vào AI model để dự đoán
                    try:
                        feature_vector = [temp, co2, smoke] # Tùy schema của AI
                        prediction = ai_detector.predict([feature_vector])
                        # Nếu AI báo bất thường, ghi ra file log
                        if prediction[0] == -1: 
                            with open('logs/alert_events.jsonl', 'a') as f:
                                alert = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "alert_id": f"AI_ALERT_{int(time.time())}", "location": room, "severity": "critical", "message": "AI Isolation Forest detected anomaly!"}
                                f.write(json.dumps(alert) + '\n')
                    except:
                        pass
                # -----------------------------------------------

                entities.extend([
                    {"id": f"Device:TEMP_{room}", "type": "TemperatureSensor", "temperature": temp},
                    {"id": f"Device:AIR_{room}", "type": "AirQualitySensor", "co2": co2},
                    {"id": f"Device:SMOKE_{room}", "type": "SmokeDetector", "smoke_status": smoke}
                ])

            self.wfile.write(json.dumps(entities).encode())
            return

        # 3. Phục vụ các file tĩnh (HTML, JS, CSS)
        else:
            super().do_GET()

with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
    print(f"🚀 DNTU Command Center Server đang chạy tại http://localhost:{PORT}")
    print(f"👉 Hãy mở trình duyệt và truy cập: http://localhost:{PORT}/dashboard.html")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã tắt Server.")