"""
Các lệnh điều khiển thiết bị thông minh Tuya
Support: Smart Plug, Audible Alarm, Door Lock
"""

from .client import TuyaCloudClient


class SmartPlugController:
    """Điều khiển ổ cắm thông minh Tuya"""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        self._client = TuyaCloudClient(device_id)
    
    @property
    def client(self):
        return self._client
    
    def turn_on(self) -> dict:
        """Bật ổ cắm"""
        return self.client.send_command("switch_1", True)
    
    def turn_off(self) -> dict:
        """Tắt ổ cắm"""
        return self.client.send_command("switch_1", False)
    
    def get_switch_state(self) -> bool:
        """Lấy trạng thái bật/tắt"""
        status = self.client.get_status()
        return status.get("switch_1", False)
    
    def get_power(self) -> float:
        """Lấy công suất tiêu thụ (W)"""
        status = self.client.get_status()
        return status.get("cur_power", 0)
    
    def get_all_status(self) -> dict:
        """Lấy tất cả thông số"""
        return self.client.get_status()
    
    def toggle(self) -> dict:
        """Đảo trạng thái bật/tắt"""
        current = self.get_switch_state()
        if current:
            return self.turn_off()
        else:
            return self.turn_on()


class AudibleAlarmController:
    """Điều khiển loa báo động / còi báo Tuya"""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        self._client = TuyaCloudClient(device_id)
    
    @property
    def client(self):
        return self._client
    
    def turn_on(self, alarm_type: int = 10, duration: int = 10) -> dict:
        """
        Bật loa báo động
        
        Args:
            alarm_type: Loại âm thanh (4,6,10,16,17,18) - mặc định 10
            duration: Thời gian kêu (giây, 0-1800) - mặc định 10 giây
        """
        # Gửi đồng thời nhiều lệnh
        commands = [
            {"code": "AlarmType", "value": alarm_type},
            {"code": "AlarmPeriod", "value": duration},
            {"code": "AlarmSwitch", "value": True}  # Boolean Python
        ]
        payload = {"commands": commands}
        return self.client.cloud.sendcommand(self.device_id, payload)
    
    def turn_off(self) -> dict:
        """Tắt loa báo động ngay lập tức"""
        commands = [{"code": "AlarmSwitch", "value": False}]
        payload = {"commands": commands}
        return self.client.cloud.sendcommand(self.device_id, payload)
    
    def get_alarm_state(self) -> bool:
        """Lấy trạng thái bật/tắt của loa"""
        status = self.client.get_status()
        return status.get("AlarmSwitch", False)
    
    def get_all_status(self) -> dict:
        """Lấy tất cả thông số"""
        return self.client.get_status()
    
    # Các phương thức cảnh báo nhanh
    def fire_alert(self) -> dict:
        """Cảnh báo cháy"""
        return self.turn_on(alarm_type=10, duration=60)
    
    def emergency_alert(self) -> dict:
        """Cảnh báo khẩn cấp"""
        return self.turn_on(alarm_type=4, duration=30)
    
    def intrusion_alert(self) -> dict:
        """Cảnh báo xâm nhập"""
        return self.turn_on(alarm_type=17, duration=20)


class DoorLockController:
    """Điều khiển khóa cửa thông minh Tuya (C100-F)"""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        self._client = TuyaCloudClient(device_id)
    
    @property
    def client(self):
        return self._client
    
    def lock(self) -> dict:
        """Khóa cửa (manual_lock = true)"""
        return self.client.send_command("manual_lock", True)
    
    def unlock(self) -> dict:
        """Mở khóa cửa (manual_lock = false)"""
        return self.client.send_command("manual_lock", False)
    
    def get_lock_state(self) -> bool:
        """Lấy trạng thái khóa (True = đang khóa, False = đang mở)"""
        status = self.client.get_status()
        return status.get("manual_lock", True)
    
    def enable_auto_lock(self, delay_seconds: int = 5) -> dict:
        """
        Bật tính năng tự động khóa
        
        Args:
            delay_seconds: Thời gian delay trước khi tự động khóa (3-15 giây)
        """
        if not 3 <= delay_seconds <= 15:
            raise ValueError("delay_seconds phải từ 3 đến 15 giây")
        self.client.send_command("automatic_lock", True)
        return self.client.send_command("auto_lock_time", delay_seconds)
    
    def disable_auto_lock(self) -> dict:
        """Tắt tính năng tự động khóa"""
        return self.client.send_command("automatic_lock", False)
    
    def get_auto_lock_status(self) -> dict:
        """Lấy trạng thái cài đặt tự động khóa"""
        status = self.client.get_status()
        return {
            "enabled": status.get("automatic_lock", False),
            "delay_seconds": status.get("auto_lock_time", 5)
        }
    
    def get_battery_state(self) -> str:
        """Lấy trạng thái pin"""
        status = self.client.get_status()
        battery = status.get("battery_state", "unknown")
        # Chuyển đổi giá trị sang text dễ hiểu
        battery_map = {"high": "Cao (>60%)", "medium": "Trung bình (30-60%)", "low": "Thấp (<30%)"}
        return battery_map.get(str(battery), "Không xác định")
    
    def get_all_status(self) -> dict:
        """Lấy tất cả thông số"""
        return self.client.get_status()
    
    def toggle(self) -> dict:
        """Đảo trạng thái khóa/mở khóa"""
        current = self.get_lock_state()
        if current:
            return self.unlock()
        else:
            return self.lock()