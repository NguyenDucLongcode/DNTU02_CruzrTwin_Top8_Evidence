"""
Điều khiển ổ cắm Tuya từ FIWARE device_id

Cách dùng:
    python scripts/tools/control_iot/control_smart_plug_a106.py on
    python scripts/tools/control_iot/control_smart_plug_a106.py off
    python scripts/tools/control_iot/control_smart_plug_a106.py status
"""

import argparse
import json
import sys
from pathlib import Path

# Thêm đường dẫn
ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

from src.tuya import get_adapter

# Dùng FIWARE device_id (từ file config)
FIWARE_DEVICE_ID = "smart_plug_a106"


def main():
    parser = argparse.ArgumentParser(description="Điều khiển ổ cắm thông minh Tuya")
    parser.add_argument("action", choices=["on", "off", "status", "toggle", "list"])
    args = parser.parse_args()
    
    # Lấy adapter
    adapter = get_adapter()
    
    if args.action == "list":
        devices = adapter.list_devices()
        print(json.dumps(devices, indent=2, ensure_ascii=False))
        return
    
    if args.action == "status":
        status = adapter.get_status(FIWARE_DEVICE_ID)
        print(json.dumps(status, indent=2, ensure_ascii=False))
        
    elif args.action == "on":
        result = adapter.turn_on(FIWARE_DEVICE_ID)
        print(f"✅ BẬT ổ cắm {FIWARE_DEVICE_ID}")
        
    elif args.action == "off":
        result = adapter.turn_off(FIWARE_DEVICE_ID)
        print(f"✅ TẮT ổ cắm {FIWARE_DEVICE_ID}")
        
    elif args.action == "toggle":
        status = adapter.get_status(FIWARE_DEVICE_ID)
        current = status.get("switch_1", False)
        if current:
            adapter.turn_off(FIWARE_DEVICE_ID)
            print(f"✅ ĐẢO TRẠNG THÁI: TẮT {FIWARE_DEVICE_ID}")
        else:
            adapter.turn_on(FIWARE_DEVICE_ID)
            print(f"✅ ĐẢO TRẠNG THÁI: BẬT {FIWARE_DEVICE_ID}")


if __name__ == "__main__":
    main()