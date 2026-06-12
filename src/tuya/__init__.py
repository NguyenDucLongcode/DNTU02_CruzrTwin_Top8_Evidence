"""
Các lệnh điều khiển ổ cắm thông minh Tuya
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