"""
Điều khiển loa báo động Tuya từ FIWARE device_id (dùng adapter)
"""

import argparse
import json
import sys
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
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
        success = result.get("success", False) if isinstance(result, dict) else False
        status_msg = "[SUCCESS] BẬT thành công" if success else "[FAILED] BẬT thất bại"
        print(f"{status_msg} loa {FIWARE_DEVICE_ID}:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    elif args.action == "off":
        result = adapter.turn_off(FIWARE_DEVICE_ID)
        success = result.get("success", False) if isinstance(result, dict) else False
        status_msg = "[SUCCESS] TẮT thành công" if success else "[FAILED] TẮT thất bại"
        print(f"{status_msg} loa {FIWARE_DEVICE_ID}:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    elif args.action == "toggle":
        status = adapter.get_status(FIWARE_DEVICE_ID)
        current = status.get("AlarmSwitch", False)
        if current:
            result = adapter.turn_off(FIWARE_DEVICE_ID)
            success = result.get("success", False) if isinstance(result, dict) else False
            status_msg = "[SUCCESS] ĐẢO (TẮT) thành công" if success else "[FAILED] ĐẢO (TẮT) thất bại"
            print(f"{status_msg} loa {FIWARE_DEVICE_ID}:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            result = adapter.turn_on(FIWARE_DEVICE_ID)
            success = result.get("success", False) if isinstance(result, dict) else False
            status_msg = "[SUCCESS] ĐẢO (BẬT) thành công" if success else "[FAILED] ĐẢO (BẬT) thất bại"
            print(f"{status_msg} loa {FIWARE_DEVICE_ID}:")
            print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()