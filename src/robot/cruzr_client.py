"""
Cruzr Robot Client - Điều khiển robot thật qua WebSocket
"""

import os
import json
import time
import threading
import logging
import queue
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import websocket
from dotenv import load_dotenv

# Tự động nạp file .env từ thư mục gốc dự án
load_dotenv()

logger = logging.getLogger(__name__)

GLOBAL_MOVEMENT_STOPPED = False

def set_global_movement_stopped(status: bool = True):
    global GLOBAL_MOVEMENT_STOPPED
    GLOBAL_MOVEMENT_STOPPED = status
    print(f"🛑 [CRUZR CLIENT] GLOBAL_MOVEMENT_STOPPED = {status}")

def toggle_global_movement_stopped() -> bool:
    """Đảo trạng thái dừng/tiếp tục di chuyển của Robot (Toggle Movement Pause/Resume)"""
    global GLOBAL_MOVEMENT_STOPPED
    GLOBAL_MOVEMENT_STOPPED = not GLOBAL_MOVEMENT_STOPPED
    status_str = "DỪNG (PAUSED)" if GLOBAL_MOVEMENT_STOPPED else "TIẾP TỤC (RESUMED)"
    print(f"🔄 [CRUZR CLIENT] Đã chuyển trạng thái di chuyển Robot: {status_str}")
    return GLOBAL_MOVEMENT_STOPPED


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
        self.ip = ip or os.getenv("CRUZR_IP", "192.168.1.107")
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

    def connect(self, timeout: float = 0.5) -> bool:
        """Kết nối đến robot"""
        if self._connected and self._ws:
            return True

        try:
            self._ws = websocket.create_connection(self.url, timeout=timeout)
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
            # ★ FIX: Flush response cũ bị kẹt trong queue trước khi gửi lệnh mới
            flushed = 0
            while not self._response_queue.empty():
                try:
                    self._response_queue.get_nowait()
                    flushed += 1
                except queue.Empty:
                    break
            if flushed:
                print(f"   \U0001f9f9 [QUEUE] Flush {flushed} stale response(s) trước '{command}'")

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

    def move(self, distance=0,movingAngle=0,turningSpeed=0,turningAngle=0, speed= 0,) -> Dict:
        """
        Di chuyển robot
        """
        if GLOBAL_MOVEMENT_STOPPED:
            print("🛑 [MOVEMENT STOPPED] Bánh xe đã dừng theo lệnh Nút 8 (Vẫn giữ âm thanh, thoại & IoT).")
            return {"success": True, "message": "Movement stopped by user"}
        options = json.dumps({"movingSpeed": speed, "movingDistance": distance, "movingAngle":movingAngle,"turningSpeed": turningSpeed,"turningAngle":turningAngle})
        return self.send_command("key_move_input", options)

    def move_forward(self, speed: float = 0.5 ) -> Dict:
        return self.move("move_forward", speed)

    def move_backward(self, speed: float = 0.5) -> Dict:
        return self.move("move_back", speed)

    def move_left(self, speed: float = 0.5) -> Dict:
        return self.move("move_forward_left", speed)

    def move_right(self, speed: float = 0.5) -> Dict:
        return self.move("move_forward_right", speed)

    def turn_left(self, speed: float = 0.5) -> Dict:
        return self.move("rotate_left", speed)

    def turn_right(self, speed: float = 0.5) -> Dict:
        return self.move("rotate_right", speed)

    def stop_move(self) -> Dict:
        """Dừng di chuyển bánh xe Robot ngay lập tức (Gửi movingSpeed: 0, turningSpeed: 0)"""
        options = json.dumps({"movingSpeed": 0.0, "movingDistance": 0.0, "movingAngle": 0.0, "turningSpeed": 0.0, "turningAngle": 0.0})
        print("🛑 Gửi lệnh dừng di chuyển bánh xe tới Robot...")
        return self.send_command("key_move_input", options)

    def stop(self) -> Dict:
        return self.stop_move()

    def _move_for_distance(self, direction: str, distance_m: float, speed: float = 0.5) -> Dict:
        """Di chuyển theo hướng trong khoảng thời gian ước lượng từ quãng đường."""
        speed = max(speed, 0.1)
        duration = distance_m / speed
        result = self.move(direction, speed)
        time.sleep(duration)
        self.stop()
        return result


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

    def speak_and_wait(self, text: str, language: str = "vi", fallback_timeout: float = None) -> Dict:
        """
        Phát giọng nói (TTS) và CHỜ robot nói xong.
        Kết hợp: chờ response 'completed' từ robot + ước lượng thời gian dựa trên text.
        Dùng thay cho speak() + time.sleep() cố định.
        """
        result = self.speak(text, language)

        if not result.get("success", False):
            print(f"   ❌ [SPEAK] Lệnh speak thất bại: {result.get('message', 'Unknown')}")
            return result

        # Ước lượng thời gian dựa trên text
        estimated = self._estimate_speak_duration(text, language)
        wait_time = max(estimated, fallback_timeout) if fallback_timeout is not None else estimated

        print(f"   ⏳ [SPEAK] Chờ robot nói ({wait_time:.1f}s, ước lượng={estimated:.1f}s)...")

        # Chờ và kiểm tra response 'completed' từ robot để thoát sớm
        deadline = time.monotonic() + wait_time
        while time.monotonic() < deadline:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                resp = self._response_queue.get(timeout=min(remaining, 0.5))
                resp_status = resp.get("status", "")
                if resp_status == "completed":
                    elapsed = wait_time - remaining
                    print(f"   ✅ [SPEAK] Robot nói xong! (sau {elapsed:.1f}s, sớm hơn {remaining:.1f}s)")
                    time.sleep(0.3)  # Buffer nhỏ để robot ổn định
                    return result
            except queue.Empty:
                continue

        print(f"   ⏱️ [SPEAK] Đã chờ hết {wait_time:.1f}s (fallback timeout)")
        time.sleep(0.2)  # Buffer nhỏ
        return result

    @staticmethod
    def _estimate_speak_duration(text: str, language: str = "vi") -> float:
        """
        Ước lượng thời gian robot nói dựa trên độ dài text.
        - Tiếng Việt: ~0.55 giây/từ
        - Tiếng Anh: ~0.45 giây/từ
        - Cộng thêm startup TTS + ngắt nghỉ dấu câu
        """
        import re
        word_count = len(text.split())
        sec_per_word = 0.55 if language.lower() == "vi" else 0.45
        startup = 1.5  # Thời gian khởi động engine TTS
        estimated = (word_count * sec_per_word) + startup
        punct_count = len(re.findall(r'[.,!?;:\-()]', text))
        estimated += punct_count * 0.3
        return max(2.0, round(estimated, 1))

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
        return self.send_command("play_emotion", json.dumps({"path": emotion_id}))

    def get_emotions(self) -> Dict:
        """Lấy danh sách emotions"""
        return self.send_command("emotions")

    def play_action(self, action_id: str) -> Dict:
        """Chơi cử chỉ/động tác tay (action/gesture)"""
        print(f"   👋 play_action: {action_id}")
        return self.send_command("play_action", json.dumps({"uri": action_id}))

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
