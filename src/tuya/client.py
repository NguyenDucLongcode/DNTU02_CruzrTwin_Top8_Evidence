"""
Kết nối và giao tiếp với Tuya Cloud API
"""

import tinytuya
from .config import load_tuya_credentials


def create_cloud_client(device_id: str = None):
    """
    Tạo kết nối đến Tuya Cloud
    
    Args:
        device_id: ID thiết bị (tùy chọn, dùng để log)
    
    Returns:
        tinytuya.Cloud: Cloud client
    """
    creds = load_tuya_credentials()
    
    return tinytuya.Cloud(
        apiRegion=creds["region"],
        apiKey=creds["key"],
        apiSecret=creds["secret"],
        apiDeviceID=device_id,
    )


class TuyaCloudClient:
    """Wrapper cho Tuya Cloud API"""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        self._cloud = None
    
    @property
    def cloud(self):
        if self._cloud is None:
            self._cloud = create_cloud_client(self.device_id)
        return self._cloud
    
    def get_status(self) -> dict:
        """Lấy trạng thái thiết bị"""
        result = self.cloud.getstatus(self.device_id)
        items = result.get("result", [])
        return {item["code"]: item["value"] for item in items}
    
    def send_command(self, code: str, value) -> dict:
        """Gửi lệnh đến thiết bị"""
        payload = {"commands": [{"code": code, "value": value}]}
        return self.cloud.sendcommand(self.device_id, payload)