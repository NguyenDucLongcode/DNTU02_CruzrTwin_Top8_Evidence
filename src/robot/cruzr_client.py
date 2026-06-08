"""
Cruzr Robot Client - Điều khiển robot thật qua WebSocket
"""

import os
import json
import time
import threading
import logging
import queue
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import websocket

logger = logging.getLogger(__name__)


class MoveDirection(Enum):
    """Hướng di chuyển"""
    FORWARD = "forward"
    BACKWARD = "back"
    LEFT = "left"
    RIGHT = "right"
    STOP = "stop"


@dataclass
class RobotStatus:
    """Trạng thái robot"""
    battery_level: int = 100
    is_charging: bool = False
    current_x: float = 0
    current_y: float = 0
    current_angle: float = 0
    current_map: str = ""
    connected: bool = False


class CruzrRobotClient:
    """
    Client kết nối đến robot Cruzr thật qua WebSocket
    
    Cách dùng:
        robot = CruzrRobotClient()
        robot.connect()
        robot.move_forward(speed=0.5)
        robot.speak("Xin chào")
        robot.disconnect()
    """
    
    def __init__(self, ip: str = None, port: int = 5000, token: str = None):
        """
        Args:
            ip: Địa chỉ IP của robot (VD: 192.168.1.100)
            port: Cổng WebSocket (mặc định 5000)
            token: Token xác thực (mặc định MY_SECRET_TOKEN)
        """
        self.ip = ip or os.getenv("CRUZR_IP", "192.168.52.119")
        self.port = port
        self.token = token or os.getenv("CRUZR_TOKEN", "MY_SECRET_TOKEN")
        self.url = f"ws://{self.ip}:{self.port}?token={self.token}"
        
        # Trạng thái kết nối và WebSocket 
        self._ws = None  # WebSocket connection
        self._connected = False # Cờ kết nối
        self._event_handlers: Dict[str, Callable] = {} # Handlers cho push events
        self._status = RobotStatus() # Trạng thái robot hiện tại
        self._receive_thread = None # Thread nhận message từ robot
        self._response_queue: "queue.Queue[dict]" = queue.Queue() # Queue để nhận phản hồi command
        self._command_lock = threading.Lock() # Lock để đồng bộ gửi command và nhận response
        
    def is_connected(self) -> bool:
        """Kiểm tra kết nối"""
        return self._connected and self._ws is not None

    def connect(self) -> bool:
        """Kết nối đến robot"""
        if self._connected and self._ws:
            return True

        try:
            self._ws = websocket.create_connection(self.url, timeout=10)
            self._connected = True
            
            # Khởi động thread nhận mọi message từ robot; response command được tách ra qua queue
            self._receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._receive_thread.start()
            
            logger.info(f"✅ Connected to Cruzr robot at {self.ip}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Ngắt kết nối"""
        self._connected = False
        if self._ws:
            self._ws.close()
            self._ws = None
        logger.info("🔌 Disconnected from Cruzr robot")
    
    def _receive_loop(self):
        """Nhận cả push events lẫn phản hồi command từ robot"""
        while self._connected and self._ws:
            try:
                self._ws.settimeout(1.0)
                message = self._ws.recv()
                if message:
                    data = json.loads(message)
                    if isinstance(data, dict) and "success" in data:
                        self._response_queue.put(data)
                    else:
                        self._handle_push_event(data)
            except websocket.WebSocketTimeoutException:
                continue
            except Exception as e:
                if self._connected:
                    logger.error(f"Listen error: {e}")
                break
    
    def _handle_push_event(self, data: dict):
        """Xử lý push event từ robot"""
        event_type = data.get("type", "")
        
        if event_type == "power_change":
            self._status.battery_level = data.get("battery_level", 100)
            self._status.is_charging = data.get("charging", False)
            logger.info(f"🔋 Battery: {self._status.battery_level}%")
            
        elif event_type == "current_location":
            self._status.current_x = data.get("x", 0)
            self._status.current_y = data.get("y", 0)
            self._status.current_angle = data.get("angle", 0)
            self._status.current_map = data.get("mapId", "")
            logger.info(f"📍 Location: ({self._status.current_x}, {self._status.current_y})")
        
        # Gọi handler nếu có
        if event_type in self._event_handlers:
            self._event_handlers[event_type](data)
    
    def on(self, event: str, handler: Callable):
        """Đăng ký handler cho push event"""
        self._event_handlers[event] = handler
    
    def send_command(self, command: str, options: Any = None, timeout: float = 10.0) -> Dict:
        """
        Gửi lệnh đến robot
        
        Args:
            command: Tên lệnh (VD: "stream_move_input", "current_location")
            options: Tham số (dict, string, hoặc None)
        
        Returns:
            Dict: Phản hồi từ robot
        """
        if not self._connected:
            if not self.connect():
                return {"success": False, "message": "Not connected"}
        
        payload = {"command": command}
        if options is not None:
            payload["options"] = options
        
        with self._command_lock:
            try:
                self._ws.send(json.dumps(payload))

                deadline = time.monotonic() + timeout
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        return {"success": False, "message": f"Timeout waiting for response to '{command}'"}

                    try:
                        response = self._response_queue.get(timeout=remaining)
                        return response
                    except queue.Empty:
                        continue

            except Exception as e:
                logger.error(f"Command '{command}' failed: {e}")
                return {"success": False, "message": str(e)}
    
    # ==================================================
    # ROBOT CONTROL COMMANDS
    # ==================================================
    
    def move(self, direction: str, speed: float = 0.5) -> Dict:
        """Di chuyển robot"""
        if direction == "stop":
            return self.send_command("stream_move_input", {"direction": "stop"})
        return self.send_command("stream_move_input", {"direction": direction, "speed": speed})
    
    def move_forward(self, speed: float = 0.5) -> Dict:
        return self.move("forward", speed)
    
    def move_backward(self, speed: float = 0.5) -> Dict:
        return self.move("back", speed)
    
    def turn_left(self, speed: float = 0.5) -> Dict:
        return self.move("left", speed)
    
    def turn_right(self, speed: float = 0.5) -> Dict:
        return self.move("right", speed)
    
    def stop(self) -> Dict:
        return self.move("stop")
    
    def speak(self, text: str, language: str = "vi") -> Dict:
        """
        Phát giọng nói (Text-to-Speech)
    
        Định dạng đúng theo yêu cầu của robot:
        {
            "command": "play_voice_response",
            "options": "{\"language\":\"vi\",\"text\":\"Xin chào\"}"
        }
        """
        options = json.dumps({"language": language, "text": text})
        print(f"gửi lệnh speak: {options}")
        return self.send_command("play_voice_response", options)
    
    def set_volume(self, volume: int) -> Dict:
        """Đặt âm lượng (0-100)"""
        return self.send_command("set_volume", volume)
    
    def get_volume(self) -> Dict:
        """Lấy âm lượng hiện tại"""
        return self.send_command("volume")
    
    def shutdown(self) -> Dict:
        """Tắt robot"""
        return self.send_command("shutdown")
    
    # ==================================================
    # NAVIGATION COMMANDS
    # ==================================================
    
    def get_current_location(self) -> Dict:
        """Lấy vị trí hiện tại"""
        return self.send_command("current_location")
    
    def get_maps(self) -> Dict:
        """Lấy danh sách bản đồ"""
        return self.send_command("maps")
    
    def use_map(self, map_id: str) -> Dict:
        """Tải và sử dụng bản đồ"""
        return self.send_command("use_map", map_id)
    
    def navigate_to(self, x: float, y: float, map_id: str = None) -> Dict:
        """Di chuyển đến tọa độ"""
        options = {"targetX": x, "targetY": y}
        if map_id:
            options["mapId"] = map_id
        return self.send_command("navigate", options)
    
    def locate_self(self) -> Dict:
        """Định vị robot trên bản đồ"""
        return self.send_command("locate_self")
    
    # ==================================================
    # EMOTION COMMANDS
    # ==================================================
    
    def play_emotion(self, emotion_id: str) -> Dict:
        """Chơi emotion"""
        return self.send_command("play_emotion", emotion_id)
    
    def get_emotions(self) -> Dict:
        """Lấy danh sách emotions"""
        return self.send_command("emotions")
    
    def dismiss_emotion(self) -> Dict:
        """Tắt emotion hiện tại"""
        return self.send_command("dismiss_emotion")
    
    # ==================================================
    # EMERGENCY (CHO KỊCH BẢN CHÁY)
    # ==================================================
    
    def emergency_evacuation(self, room: str = "A101") -> Dict:
        """
        Phát cảnh báo cháy khẩn cấp
        Đây là lệnh quan trọng nhất cho demo của bạn
        """
        message = f"⚠️ CẢNH BÁO CHÁY tại phòng {room}! Vui lòng sơ tán khẩn cấp theo lối thoát hiểm! ⚠️"
        print(f"dã chay vao robot!")
        
        # Phát voice cảnh báo
        self.speak(message)
        
        # Chơi emotion khẩn cấp (nếu có)
        self.play_emotion("emergency")
        
        # Quay về emotion mặc định sau 5 giây
        time.sleep(5)
        self.dismiss_emotion()
        
        return {"status": "dispatched", "message": message}
    
    # ==================================================
    # GET STATUS
    # ==================================================
    
    def get_status(self) -> RobotStatus:
        """Lấy trạng thái hiện tại của robot"""
        return self._status
    
    def is_connected(self) -> bool:
        """Kiểm tra kết nối"""
        return self._connected