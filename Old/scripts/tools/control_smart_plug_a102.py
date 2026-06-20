"""
Điều khiển ổ cắm Tuya thật

Cách dùng:
    python scripts/tools/control_smart_plug.py on
    python scripts/tools/control_smart_plug.py off
    python scripts/tools/control_smart_plug.py status
"""

import argparse
import json
import sys
from pathlib import Path

# Thêm đường dẫn
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from src.tuya import SmartPlugController

# ID thiết bị Tuya (từ web)
TUYA_DEVICE_ID = "a38764792570512f2fgnnz"
IOT_DEVICE_ID = "smart_plug_a102"


def main():
    parser = argparse.ArgumentParser(description="Điều khiển ổ cắm thông minh Tuya")
    parser.add_argument("action", choices=["on", "off", "status", "toggle"])
    args = parser.parse_args()
    
    # Tạo controller
    plug = SmartPlugController(TUYA_DEVICE_ID)
    
    if args.action == "status":
        status = plug.get_all_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
        
    elif args.action == "on":
        result = plug.turn_on()
        print(f"✅ BẬT ổ cắm {IOT_DEVICE_ID}")
        print(f"Kết quả: {result}")
        
    elif args.action == "off":
        result = plug.turn_off()
        print(f"✅ TẮT ổ cắm {IOT_DEVICE_ID}")
        print(f"Kết quả: {result}")
        
    elif args.action == "toggle":
        result = plug.toggle()
        state = plug.get_switch_state()
        print(f"✅ ĐẢO TRẠNG THÁI: {'BẬT' if state else 'TẮT'}")
        print(f"Kết quả: {result}")


if __name__ == "__main__":
    main()