"""
Điều khiển loa báo động Tuya từ FIWARE device_id (dùng adapter)
"""

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

from src.tuya import get_adapter

FIWARE_DEVICE_ID = "audible_alarm_a101"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["on", "off", "status", "toggle", "list"])
    args = parser.parse_args()
    
    adapter = get_adapter()
     
    # Nếu chỉ muốn xem danh sách thiết bị
    if args.action == "list":
        devices = adapter.list_devices()
        print(json.dumps(devices, indent=2, ensure_ascii=False))
        return
    
    if args.action == "status":
        status = adapter.get_status(FIWARE_DEVICE_ID)
        print(json.dumps(status, indent=2, ensure_ascii=False))
        
    elif args.action == "on":
        result = adapter.turn_on(FIWARE_DEVICE_ID)
        print(f"✅ BẬT loa {FIWARE_DEVICE_ID}")
        
    elif args.action == "off":
        result = adapter.turn_off(FIWARE_DEVICE_ID)
        print(f"✅ TẮT loa {FIWARE_DEVICE_ID}")
        
    elif args.action == "toggle":
        status = adapter.get_status(FIWARE_DEVICE_ID)
        current = status.get("AlarmSwitch", False)
        if current:
            adapter.turn_off(FIWARE_DEVICE_ID)
            print(f"✅ ĐẢO: TẮT {FIWARE_DEVICE_ID}")
        else:
            adapter.turn_on(FIWARE_DEVICE_ID)
            print(f"✅ ĐẢO: BẬT {FIWARE_DEVICE_ID}")


if __name__ == "__main__":
    main()