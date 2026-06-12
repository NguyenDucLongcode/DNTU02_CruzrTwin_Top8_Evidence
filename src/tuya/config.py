"""
Đọc cấu hình Tuya từ file YAML hoặc biến môi trường
"""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT_DIR / "docker" / "tuya2mqtt.yaml"


def load_tuya_credentials() -> dict:
    """
    Đọc thông tin đăng nhập Tuya
    
    Returns:
        dict: {"region": "sg", "key": "...", "secret": "..."}
    """
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Không tìm thấy config: {CONFIG_PATH}")
    
    with CONFIG_PATH.open(encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    
    tuya = config.get("tuya") or {}
    
    # Ưu tiên biến môi trường, sau đó đến file config
    region = os.getenv("TUYA_REGION", tuya.get("region", "sg"))
    key = os.getenv("TUYA_KEY", tuya.get("key"))
    secret = os.getenv("TUYA_SECRET", tuya.get("secret"))
    
    if not key or not secret:
        raise ValueError("Thiếu Tuya API key/secret trong config hoặc env")
    
    return {"region": region, "key": key, "secret": secret}


def get_device_config(device_id: str) -> dict:
    """
    Lấy cấu hình của một thiết bị từ tuya2mqtt.yaml
    
    Args:
        device_id: ID thiết bị Tuya (VD: a38764792570512f2fgnnz)
    
    Returns:
        dict: Thông tin device (name, device_id, attrs...)
    """
    with CONFIG_PATH.open(encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    
    devices = config.get("devices", [])
    for device in devices:
        if device.get("id") == device_id:
            return device
    
    return None