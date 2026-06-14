import http.server
import socketserver
import json
import random
import time
import os
import sys
import threading

# Khai báo cổng
PORT = 8000

# Thử import các module cần thiết
try:
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    from src.ai.detector import AnomalyDetector
    from src.robot.cruzr_client import CruzrRobotClient
    from src.iot.devices import DEVICES_TO_REGISTER
    
    ai_detector = AnomalyDetector()
    robot_client = CruzrRobotClient()
    # Thử kết nối robot trong background
    threading.Thread(target=robot_client.connect, daemon=True).start()
    
    print("[SYSTEM] Đã khởi tạo AI Engine và Robot Client")
    HAS_AI = True
except Exception as e:
    print(f"[SYSTEM WARNING] Lỗi khởi tạo: {e}")
    HAS_AI = False

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        if self.path == '/api/robot/command':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            cmd = json.loads(post_data)
            
            action = cmd.get('action')
            print(f"[ROBOT] Nhận lệnh: {action}")
            
            result = {"success": False, "message": "Robot not connected"}
            if 'robot_client' in globals() and robot_client.is_connected():
                if action == 'move_forward': result = robot_client.move_forward()
                elif action == 'move_backward': result = robot_client.move_backward()
                elif action == 'turn_left': result = robot_client.turn_left()
                elif action == 'turn_right': result = robot_client.turn_right()
                elif action == 'stop': result = robot_client.stop()
                elif action == 'emergency': result = robot_client.emergency_evacuation(cmd.get('room', 'A101'))
                elif action == 'speak': result = robot_client.speak(cmd.get('text', 'Hello'))
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            return

    def do_GET(self):
        # 1. API: Lấy Logs (Hỗ trợ 5 loại)
        if self.path.startswith('/api/logs/'):
            log_type = self.path.split('/')[-1]
            log_map = {
                'ai': 'logs/ai_detection.jsonl',
                'alerts': 'logs/alert_events.jsonl',
                'state': 'logs/orion_state.jsonl',
                'robot': 'logs/robot_actions.jsonl',
                'sensors': 'logs/SensorReading.jsonl'
            }
            
            file_path = log_map.get(log_type)
            logs = []
            
            if file_path and os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines[-20:]: # Lấy 20 dòng mới nhất
                        try:
                            logs.append(json.loads(line.strip()))
                        except:
                            pass
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(logs).encode())
            return

        # 2. API: Robot Status
        elif self.path == '/api/robot/status':
            status = {"connected": False, "battery": 0, "location": {"x": 0, "y": 0}}
            if 'robot_client' in globals():
                rs = robot_client.get_status()
                status = {
                    "connected": robot_client.is_connected(),
                    "battery": rs.battery_level,
                    "location": {"x": rs.current_x, "y": rs.current_y},
                    "charging": rs.is_charging
                }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())
            return
            
        # API: Get Devices from Registry
        elif self.path == '/api/devices':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            if 'DEVICES_TO_REGISTER' in globals():
                self.wfile.write(json.dumps(DEVICES_TO_REGISTER).encode())
            else:
                self.wfile.write(json.dumps([]).encode())
            return

        # API: Đọc REAL-TIME từ MongoDB Orion
        elif self.path == '/api/db/sensors':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            try:
                import pymongo
                client = pymongo.MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
                db = client['orion-cruzrtwin']
                entities = db['entities'].find({})
                
                room_data = {}
                for ent in entities:
                    ent_id = ent.get('_id', {}).get('id', '')
                    if not ent_id.startswith('Device:'): continue
                    
                    parts = ent_id.split('_', 1)
                    if len(parts) < 2: continue
                    
                    dev_type_prefix = parts[0] # Vd: Device:TEMP
                    room_id = parts[1]         # Vd: A101
                    
                    if room_id not in room_data:
                        room_data[room_id] = {"temp": 25.0, "smoke": 0.0, "co2": 400.0}
                        
                    attrs = ent.get('attrs', {})
                    if 'TEMP' in dev_type_prefix and 'temperature' in attrs:
                        room_data[room_id]['temp'] = attrs['temperature'].get('value', 25.0)
                    elif 'SMOKE' in dev_type_prefix and 'smoke_status' in attrs:
                        room_data[room_id]['smoke'] = attrs['smoke_status'].get('value', 0.0)
                    elif 'CO2' in dev_type_prefix and 'co2_level' in attrs:
                        room_data[room_id]['co2'] = attrs['co2_level'].get('value', 400.0)
                        
                self.wfile.write(json.dumps(room_data).encode())
            except Exception as e:
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # 3. Phục vụ các file tĩnh
        else:
            if self.path == '/' or self.path == '':
                self.path = '/dashboard.html'
            super().do_GET()

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        print(f"🚀 DNTU Digital Twin Server đang chạy tại http://localhost:{PORT}")
        print(f"👉 Mở trình duyệt: http://localhost:{PORT}/dashboard.html")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nĐã tắt Server.")
