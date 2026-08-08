import sys
import tinytuya
from .config import load_tuya_credentials

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


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
        import time
        t_start = time.perf_counter()
        send_time_str = time.strftime("%H:%M:%S") + f".{int((t_start % 1) * 1000):03d}"
        payload = {"commands": [{"code": code, "value": value}]}
        print(f"   ⏱️ [TUYA PAYLOAD SEND] Device: {self.device_id} | Payload: {payload} | Sent at: {send_time_str}")

        result = self.cloud.sendcommand(self.device_id, payload)

        t_end = time.perf_counter()
        recv_time_str = time.strftime("%H:%M:%S") + f".{int((t_end % 1) * 1000):03d}"
        elapsed_ms = (t_end - t_start) * 1000
        print(f"   ⏱️ [TUYA RESPONSE RECV] Device: {self.device_id} | Recv at: {recv_time_str} | Latency: {elapsed_ms:.2f} ms ({elapsed_ms/1000:.2f}s)")
        return result