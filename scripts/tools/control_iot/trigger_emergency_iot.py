import os
import sys
import json
import argparse
from pathlib import Path

# Thêm đường dẫn gốc dự án
ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

from src.tuya import control_multiple_by_fiware_ids
from src.fiware import get_smart_plugs_in_room, get_alarms_in_room

# Cấu hình UTF-8 cho Windows console
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def trigger_emergency_iot(zone_id: str = "DNTU_ROOM_A101", action: str = "critical"):
    """
    Thực thi độc lập các lệnh Tuya IoT (Smart Plugs & Alarms) cho một phòng
    - action = "critical": Tắt điện Smart Plug, Bật Còi báo động
    - action = "normal": Bật lại điện Smart Plug, Tắt Còi báo động
    """
    print("\n" + "=" * 60)
    print(f"🔌 EMERGENCY IOT EXECUTION SCRIPT ({action.upper()})")
    print(f"📍 Zone ID: {zone_id}")
    print("=" * 60)

    smart_plugs = get_smart_plugs_in_room(zone_id)
    alarms = get_alarms_in_room(zone_id)

    plug_action = "off" if action.lower() == "critical" else "on"
    alarm_action = "on" if action.lower() == "critical" else "off"

    results = {}

    # 1. Điều khiển Smart Plugs
    if smart_plugs:
        print(f"\n⚡ [SMART PLUG] Đang gửi lệnh [{plug_action.upper()}] tới {len(smart_plugs)} ổ cắm điện...")
        res_plugs = control_multiple_by_fiware_ids(
            fiware_ids=smart_plugs,
            action=plug_action,
            device_type="smart_plug",
            max_workers=len(smart_plugs)
        )
        results["smart_plugs"] = res_plugs

    # 2. Điều khiển Còi báo động Alarms
    if alarms:
        print(f"\n🚨 [ALARM] Đang gửi lệnh [{alarm_action.upper()}] tới {len(alarms)} còi báo động...")
        res_alarms = control_multiple_by_fiware_ids(
            fiware_ids=alarms,
            action=alarm_action,
            device_type="alarm",
            alarm_type=10 if alarm_action == "on" else 0,
            duration=60 if alarm_action == "on" else 0,
            max_workers=len(alarms)
        )
        results["alarms"] = res_alarms

    print("\n✅ Hoàn thành thực thi lệnh IoT!")
    return results


def main():
    parser = argparse.ArgumentParser(description="Script điều khiển độc lập các thiết bị IoT theo sự cố")
    parser.add_argument("--zone", default="DNTU_ROOM_A101", help="Mã phòng (mặc định: DNTU_ROOM_A101)")
    parser.add_argument("--action", choices=["critical", "normal", "undo"], default="critical", help="Hành động: critical (tắt điện, bật còi) hoặc normal (bật lại điện, tắt còi)")
    args = parser.parse_args()

    res = trigger_emergency_iot(zone_id=args.zone, action=args.action)
    print("\n--- KẾT QUẢ ---")
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
