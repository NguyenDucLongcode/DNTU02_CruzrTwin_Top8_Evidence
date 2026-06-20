import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from src.tuya import control_multiple_by_fiware_ids
from src.fiware import get_smart_plugs_in_room, get_alarms_in_room
from .cruzr_client import CruzrRobotClient
import time
# Import translator utility
from src.utils import translate_to_vietnamese, speak_sequence, estimate_speak_duration, wait_for_robot_ready


# Lưu các action đã thực hiện trong phiên chạy hiện tại
_created_robot_actions = set()



def append_jsonl(path: str, data: dict):
    """
    Ghi log JSONL
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


def get_utc_timestamp() -> str:
    """
    Trả về timestamp dạng ISO8601 UTC:
    2026-06-17T09:00:25Z
    """
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )




def main(alert_event: dict) -> dict:
    """
    Khi có cảnh báo critical:
    - Tắt tất cả smart plug trong phòng
    - Bật tất cả alarm
    - Ghi log RobotAction
    - Không thực hiện lại nếu action đã được tạo
    """

    demo_run_id = alert_event["demo_run_id"]
    alert_id = alert_event["alert_id"]
    scenario_id = alert_event["scenario_id"]
    zone_id = alert_event["zone_id"]
    severity = alert_event.get("severity", "critical")
    # message cảnh báo của ai

    room_name = zone_id.split("_")[-1]
    # messageCitical = alert_event.get("message", "")
    messageCitical = (
        f"Critical indoor-environment anomaly detected in "
        f"Room {room_name}. Please follow staff guidance and move calmly to the safe waiting area. "
    )
    vi_messageCitical = translate_to_vietnamese(messageCitical)

    # message tắt smart plug và bật alarm
    messageSmartPlug = "Turn off all electrical devices."
    vi_messageSmartPlug = translate_to_vietnamese(messageSmartPlug)

    messageAlarm = "activate the alarm.."
    vi_messageAlarm = translate_to_vietnamese(messageAlarm)

    languages = ["vi", "en"]
    robot_action_id = f"RobotAction:{scenario_id}"


    # Không tạo lại action
    if robot_action_id in _created_robot_actions:
        return {
            "status": "skipped",
            "reason": "Action already executed",
            "robot_action_id": robot_action_id,
            "zone_id": zone_id
        }

    # Chỉ xử lý cảnh báo critical
    if severity.lower() != "critical":
        return {
            "status": "skipped",
            "reason": f"severity={severity}",
            "zone_id": zone_id
        }

    # Đánh dấu đã xử lý
    _created_robot_actions.add(robot_action_id)

    # ============================================
# TẠO MESSAGE VÀ DỊCH SANG TIẾNG VIỆT
    # ============================================
    room_name = zone_id.split("_")[-1]

    # Khởi tạo robot client
    RobotClient = CruzrRobotClient()

    isConnected =  RobotClient.connect()

    # Kết nối nếu chưa kết nối
    if not isConnected:
        print("   🤖 Robot not connected. Trying to connect...")
        return False

     # Robot log
    log_entry = {
        "demo_run_id": demo_run_id,
        "timestamp": get_utc_timestamp(),
        "robot_id": "CRUZR_01",
        "alert_id": alert_id,
        "zone_id": zone_id,
        "action_type": "VOICE_DISPLAY_GUIDANCE",
        "navigation_mode": "PREDEFINED_RESPONSE_POINT",
        "message": messageCitical,
        "status": "ACK"
    }

    log_path = ROOT_DIR / "logs" / "robot_actions.jsonl"
    append_jsonl(str(log_path), log_entry)


    # Hiển thị emotion khẩn cấp
    result = RobotClient.play_emotion("emotion://va/techface_upset")
    print(f"   😫 Emotion result: {result}")


    RobotClient.move_forward(speed=1)
    time.sleep(5)
    RobotClient.stop()


    # ============================================
    # Speak sequence (nhiều message)
    # ============================================
    # Dịch sang tiếng Việt và chuẩn bị message cảnh báo cho người dùng
    # messageCitical = [vi_messageCitical, messageCitical]
    # speak_sequence(RobotClient, messageCitical, languages, wait_between=1.0)


    RobotClient.speak(vi_messageCitical, language="vi")
    time.sleep(12)  # Đợi message tiếng Việt kết thúc trước khi nói tiếng Anh

    RobotClient.speak(messageCitical, language="en")
    time.sleep(10)  # Đợi message tiếng Anh kết thúc



    # Lấy danh sách smart plug và alarm trong phòng
    smart_plugs = get_smart_plugs_in_room(zone_id)
    alarms = get_alarms_in_room(zone_id)


    RobotClient.speak(vi_messageSmartPlug, language="vi")
    time.sleep(4)  # Đợi message tiếng Việt kết thúc trước khi nói tiếng Anh

    RobotClient.speak(messageSmartPlug, language="en")
    time.sleep(4)  # Đợi message tiếng Anh kết thúc ( )

    # Tắt Smart Plug
    if smart_plugs:
        control_multiple_by_fiware_ids(
            fiware_ids=smart_plugs,
            action="off",
            device_type="smart_plug",
            max_workers=len(smart_plugs)
    )




    # Dịch sang tiếng Việt và chuẩn bị message bật alarm cho người dùng
    # messageAlarm = [vi_messageAlarm, messageAlarm]
    # speak_sequence(RobotClient, messageAlarm, languages, wait_between=1.0)
    # ----------
    RobotClient.speak(vi_messageAlarm, language="vi")
    time.sleep(4)  # Đợi message tiếng Việt kết thúc trước khi nói tiếng Anh

    RobotClient.speak(messageAlarm, language="en")
    time.sleep(4)  # Đợi message tiếng Anh kết thúc

    # Bật Alarm
    if alarms:
        control_multiple_by_fiware_ids(
fiware_ids=alarms,
            action="on",
            device_type="alarm",
            alarm_type=10,
            duration=60,
            max_workers=len(alarms)
    )


    return {
        "status": "success",
        "demo_run_id": demo_run_id,
        "alert_id": alert_id,
        "scenario_id": scenario_id,
        "robot_action_id": robot_action_id,
        "zone_id": zone_id,
        "smart_plugs_turned_off": len(smart_plugs),
        "alarms_activated": len(alarms),
        "robot_log": log_entry
    }


if __name__ == "__main__":
    event = {
        "demo_run_id": "DNTU02_TOP8_RUN_2026_001",
        "alert_id": "AlertEvent:SCN_CRITICAL_001",
        "scenario_id": "critical_001",
        "zone_id": "DNTU_ROOM_A101",
        "severity": "critical"
    }

    result = main(event)
    print(json.dumps(result, indent=2, ensure_ascii=False))
