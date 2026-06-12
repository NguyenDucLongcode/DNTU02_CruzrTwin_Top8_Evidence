"""
Các lệnh điều khiển ổ cắm thông minh Tuya
"""

import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed

from .client import TuyaCloudClient, create_cloud_client
from .config import CONFIG_PATH

FIRE_PLUGS_OFF = ("smart_plug_a102", "smart_plug_a103")
FIRE_PLUGS_ON = ("smart_plug_a104",)


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


def _tuya_id_by_name(name: str) -> str | None:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    for device in config.get("devices", []):
        if device.get("name") == name:
            return device.get("id")
    return None


def _send_switch(cloud, tuya_id: str, turn_on: bool) -> dict:
    payload = {"commands": [{"code": "switch_1", "value": turn_on}]}
    return cloud.sendcommand(tuya_id, payload)


def control_fire_emergency_plugs() -> dict[str, dict]:
    """
    Cảnh báo cháy: tắt a102/a103, bật a104.
    Dùng một kết nối Tuya Cloud và gửi lệnh song song.
    """
    cloud = create_cloud_client()
    tasks: list[tuple[str, str, bool]] = []

    for name in FIRE_PLUGS_OFF:
        tuya_id = _tuya_id_by_name(name)
        if tuya_id:
            tasks.append((name, tuya_id, False))

    for name in FIRE_PLUGS_ON:
        tuya_id = _tuya_id_by_name(name)
        if tuya_id:
            tasks.append((name, tuya_id, True))

    results: dict[str, dict] = {}

    def _run(name: str, tuya_id: str, turn_on: bool) -> tuple[str, bool, str | None]:
        try:
            result = _send_switch(cloud, tuya_id, turn_on)
            success = result.get("success", True) if isinstance(result, dict) else True
            return name, success, None
        except Exception as e:
            return name, False, str(e)

    with ThreadPoolExecutor(max_workers=max(len(tasks), 1)) as pool:
        futures = [pool.submit(_run, name, tuya_id, turn_on) for name, tuya_id, turn_on in tasks]
        for future in as_completed(futures):
            name, ok, err = future.result()
            results[name] = {"success": ok, "error": err}

    for name in (*FIRE_PLUGS_OFF, *FIRE_PLUGS_ON):
        if name not in results:
            results[name] = {"success": False, "error": "Không tìm thấy thiết bị trong config"}

    return results