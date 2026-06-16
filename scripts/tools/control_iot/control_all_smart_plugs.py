"""
Điều khiển tất cả ổ cắm Tuya - KHÔNG IN KẾT QUẢ
"""

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

from src.tuya import get_adapter, control_multiple_by_fiware_ids

ALL_PLUGS = [
    "smart_plug_a101",
    "smart_plug_a102",
    "smart_plug_a103",
    "smart_plug_a104",
    "smart_plug_a105",
    "smart_plug_a106",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["on", "off", "status", "toggle"])
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    
    # Gửi lệnh - không in gì
    control_multiple_by_fiware_ids(
        fiware_ids=ALL_PLUGS,
        action=args.action,
        device_type="smart_plug",
        max_workers=args.workers
    )


if __name__ == "__main__":
    main()