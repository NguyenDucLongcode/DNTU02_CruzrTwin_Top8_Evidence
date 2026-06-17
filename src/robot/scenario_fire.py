import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from src.tuya import control_multiple_by_fiware_ids
from src.fiware import get_smart_plugs_in_room, get_alarms_in_room

ZONE_ID = os.getenv("ZONE_ID", "DNTU_ROOM_A101")


def main():
    # Lấy danh sách thiết bị
    smart_plugs = get_smart_plugs_in_room(ZONE_ID)
    alarms = get_alarms_in_room(ZONE_ID)
    
    # Tắt tất cả smart_plug
    if smart_plugs:
        control_multiple_by_fiware_ids(
            fiware_ids=smart_plugs,
            action="off",
            device_type="smart_plug",
            max_workers=len(smart_plugs)
        )
    
    # Bật loa báo động
    if alarms:
        control_multiple_by_fiware_ids(
            fiware_ids=alarms,
            action="on",
            device_type="alarm",
            alarm_type=10,
            duration=60,
            max_workers=len(alarms)
        )


if __name__ == "__main__":
    main()