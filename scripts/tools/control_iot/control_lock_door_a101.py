"""
Điều khiển khóa cửa Tuya từ FIWARE device_id

Cách dùng:
    python scripts/tools/control_iot/control_lock_door_a101.py lock
    python scripts/tools/control_iot/control_lock_door_a101.py unlock
    python scripts/tools/control_iot/control_lock_door_a101.py status
    python scripts/tools/control_iot/control_lock_door_a101.py toggle
    python scripts/tools/control_iot/control_lock_door_a101.py list
"""

import argparse
import json
import sys
from pathlib import Path

# Thêm đường dẫn
ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

from src.tuya import get_adapter, DoorLockController

# Dùng FIWARE device_id (từ file tuya2mqtt.yaml)
FIWARE_DEVICE_ID = "lock_door_a101"


def get_tuya_device_id(adapter, fiware_id):
    """Lấy Tuya device_id từ FIWARE ID"""
    for device in adapter.list_devices():
        if device['fiware_device_id'] == fiware_id:
            return device['tuya_device_id']
    return None


def main():
    parser = argparse.ArgumentParser(description="Điều khiển khóa cửa thông minh Tuya")
    parser.add_argument("action", choices=["lock", "unlock", "status", "toggle", "list"])
    args = parser.parse_args()
    
    # Lấy adapter
    adapter = get_adapter()
    
    if args.action == "list":
        devices = adapter.list_devices()
        print("\n=== DANH SÁCH THIẾT BỊ ===\n")
        for device in devices:
            print(f"  📱 {device['fiware_device_id']} -> {device['tuya_device_id']}")
        return
    
    # Lấy Tuya device_id thật
    tuya_device_id = get_tuya_device_id(adapter, FIWARE_DEVICE_ID)
    if not tuya_device_id:
        print(f"❌ Không tìm thấy thiết bị: {FIWARE_DEVICE_ID}")
        return
    
    # Tạo controller trực tiếp bằng Tuya ID
    lock = DoorLockController(tuya_device_id)
    
    if args.action == "status":
        status = lock.get_all_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
        
        # Hiển thị thông tin dễ đọc
        print(f"\n📊 Trạng thái khóa {FIWARE_DEVICE_ID}:")
        is_locked = status.get('manual_lock', True)
        print(f"  🔒 Trạng thái: {'🔒 ĐÃ KHÓA' if is_locked else '🔓 ĐANG MỞ'}")
        
    elif args.action == "lock":
        result = lock.lock()
        print(f"✅ KHÓA cửa {FIWARE_DEVICE_ID}")
        
    elif args.action == "unlock":
        result = lock.unlock()
        print(f"✅ MỞ KHÓA cửa {FIWARE_DEVICE_ID}")
        
    elif args.action == "toggle":
        current = lock.get_lock_state()
        if current:
            lock.unlock()
            print(f"✅ ĐẢO TRẠNG THÁI: MỞ KHÓA {FIWARE_DEVICE_ID}")
        else:
            lock.lock()
            print(f"✅ ĐẢO TRẠNG THÁI: KHÓA {FIWARE_DEVICE_ID}")


if __name__ == "__main__":
    main()