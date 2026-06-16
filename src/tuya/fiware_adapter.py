"""
Adapter để kết nối FIWARE với Tuya Cloud
Ánh xạ giữa FIWARE device_id và Tuya device_id thật
Hỗ trợ: Smart Plug, Audible Alarm, Door Lock
"""

import json
import yaml
from pathlib import Path
from typing import Optional, Dict, Union
from .commands import SmartPlugController, AudibleAlarmController, DoorLockController


class TuyaFiwareAdapter:
    """Adapter để điều khiển thiết bị Tuya từ FIWARE"""
    
    def __init__(self, config_path: str = None):
        """
        Khởi tạo adapter
        
        Args:
            config_path: Đường dẫn đến file tuya2mqtt.yaml
        """
        if config_path is None:
            current_file = Path(__file__).resolve()
            root_dir = current_file.parents[3]
            config_path = root_dir / "docker" / "tuya2mqtt.yaml"
            
            if not config_path.exists():
                for candidate in root_dir.rglob("tuya2mqtt.yaml"):
                    config_path = candidate
                    break
        
        self.config_path = Path(config_path)
        
        if not self.config_path.exists():
            raise FileNotFoundError(f"Không tìm thấy file config: {self.config_path}")
        
        self._load_mapping()
    
    def _load_mapping(self):
        """Đọc mapping từ file config"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        self.fiware_to_tuya: Dict[str, str] = {}
        self.tuya_to_fiware: Dict[str, str] = {}
        self.device_names: Dict[str, str] = {}  # Lưu tên thiết bị để phân loại
        
        for device in config.get('devices', []):
            tuya_id = device.get('id')
            fiware_id = device.get('device_id')
            name = device.get('name', fiware_id)
            
            if tuya_id and fiware_id:
                self.fiware_to_tuya[fiware_id] = tuya_id
                self.tuya_to_fiware[tuya_id] = fiware_id
                self.device_names[fiware_id] = name
    
    def get_tuya_id(self, fiware_device_id: str) -> Optional[str]:
        """Chuyển đổi từ FIWARE device_id sang Tuya device_id"""
        return self.fiware_to_tuya.get(fiware_device_id)
    
    def get_fiware_id(self, tuya_device_id: str) -> Optional[str]:
        """Chuyển đổi từ Tuya device_id sang FIWARE device_id"""
        return self.tuya_to_fiware.get(tuya_device_id)
    
    def _get_controller(self, fiware_device_id: str):
        """
        Tự động chọn đúng controller dựa trên device_id
        """
        tuya_id = self.get_tuya_id(fiware_device_id)
        if not tuya_id:
            return None
        
        # Phân loại thiết bị dựa trên tên
        name = self.device_names.get(fiware_device_id, "").lower()
        
        if "alarm" in name or "siren" in name:
            return AudibleAlarmController(tuya_id)
        elif "lock" in name or "door" in name:
            return DoorLockController(tuya_id)
        else:
            return SmartPlugController(tuya_id)
    
    # ========== Phương thức chung cho tất cả thiết bị ==========
    
    def turn_on(self, fiware_device_id: str) -> dict:
        """Bật thiết bị (smart plug hoặc loa)"""
        controller = self._get_controller(fiware_device_id)
        if controller:
            if hasattr(controller, 'turn_on'):
                return controller.turn_on()
            elif hasattr(controller, 'lock'):
                return controller.lock()  # Khóa cửa
        return {"error": f"Không tìm thấy hoặc không hỗ trợ bật: {fiware_device_id}"}
    
    def turn_off(self, fiware_device_id: str) -> dict:
        """Tắt thiết bị (smart plug hoặc loa)"""
        controller = self._get_controller(fiware_device_id)
        if controller:
            if hasattr(controller, 'turn_off'):
                return controller.turn_off()
            elif hasattr(controller, 'unlock'):
                return controller.unlock()  # Mở khóa cửa
        return {"error": f"Không tìm thấy hoặc không hỗ trợ tắt: {fiware_device_id}"}
    
    def get_status(self, fiware_device_id: str) -> dict:
        """Lấy trạng thái thiết bị"""
        controller = self._get_controller(fiware_device_id)
        if controller:
            return controller.get_all_status()
        return {"error": f"Không tìm thấy thiết bị: {fiware_device_id}"}
    
    # ========== Phương thức riêng cho khóa cửa ==========
    
    def lock(self, fiware_device_id: str) -> dict:
        """Khóa cửa"""
        controller = self._get_controller(fiware_device_id)
        if controller and hasattr(controller, 'lock'):
            return controller.lock()
        return {"error": f"Không tìm thấy hoặc không phải khóa cửa: {fiware_device_id}"}
    
    def unlock(self, fiware_device_id: str) -> dict:
        """Mở khóa cửa"""
        controller = self._get_controller(fiware_device_id)
        if controller and hasattr(controller, 'unlock'):
            return controller.unlock()
        return {"error": f"Không tìm thấy hoặc không phải khóa cửa: {fiware_device_id}"}
    
    # ========== Phương thức riêng cho loa ==========
    
    def fire_alert(self, fiware_device_id: str) -> dict:
        """Cảnh báo cháy"""
        controller = self._get_controller(fiware_device_id)
        if controller and hasattr(controller, 'fire_alert'):
            return controller.fire_alert()
        return {"error": f"Không tìm thấy hoặc không phải loa: {fiware_device_id}"}
    
    def emergency_alert(self, fiware_device_id: str) -> dict:
        """Cảnh báo khẩn cấp"""
        controller = self._get_controller(fiware_device_id)
        if controller and hasattr(controller, 'emergency_alert'):
            return controller.emergency_alert()
        return {"error": f"Không tìm thấy hoặc không phải loa: {fiware_device_id}"}
    
    def intrusion_alert(self, fiware_device_id: str) -> dict:
        """Cảnh báo xâm nhập"""
        controller = self._get_controller(fiware_device_id)
        if controller and hasattr(controller, 'intrusion_alert'):
            return controller.intrusion_alert()
        return {"error": f"Không tìm thấy hoặc không phải loa: {fiware_device_id}"}
    
    def list_devices(self) -> list:
        """Liệt kê tất cả thiết bị với cả hai loại ID"""
        devices = []
        for fiware_id, tuya_id in self.fiware_to_tuya.items():
            name = self.device_names.get(fiware_id, "")
            
            # Xác định loại thiết bị
            if "alarm" in name.lower() or "siren" in name.lower():
                device_type = "AudibleAlarm"
            elif "lock" in name.lower() or "door" in name.lower():
                device_type = "DoorLock"
            else:
                device_type = "SmartPlug"
            
            devices.append({
                "fiware_device_id": fiware_id,
                "tuya_device_id": tuya_id,
                "name": name,
                "type": device_type
            })
        return devices


# Singleton instance
_adapter_instance = None

def get_adapter() -> TuyaFiwareAdapter:
    """Lấy adapter instance (singleton)"""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = TuyaFiwareAdapter()
    return _adapter_instance