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


# Cấu hình UTF-8 cho Windows console
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Lưu các action đã thực hiện trong phiên chạy hiện tại
_created_robot_actions = set()


def reset_robot_action_cache():
    """Xóa cache các robot action đã thực hiện"""
    global _created_robot_actions
    _created_robot_actions.clear()



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

    demo_run_id = alert_event["demo_run_id"]
    alert_id = alert_event["alert_id"]
    scenario_id = alert_event["scenario_id"]
    zone_id = alert_event["zone_id"]
    severity = alert_event.get("severity", "critical")

    room_name = zone_id.split("_")[-1]
    # messageCitical = alert_event.get("message", "")
    messageCitical = f"Critical indoor-environment anomaly detected in Room {room_name}. Please follow me guidance and move calmly to the safe waiting area. "
    vi_messageCitical = f"Đã phát hiện sự cố bất thường nghiêm trọng trong môi trường trong nhà tại Phòng {room_name}. Vui lòng làm theo hướng dẫn của tôi và di chuyển bình tĩnh đến khu vực chờ an toàn. "

    # message tắt smart plug và bật alarm
    messageSmartPlug = "I will turn off all electrical devices."
    vi_messageSmartPlug = "Tôi sẽ tiến hành tắt tất cả các thiết bị điện"

    messageAlarm = "and activate the alarm.."
    vi_messageAlarm = "Và bật còi báo động"

    messageMoveOut = "Now, please follow me to the safe waiting area.."
    vi_messageMoveOut = "Bây giờ, xin hãy đi theo tôi đến khu vực chờ an toàn."

    languages = ["vi", "en"]
    robot_action_id = f"RobotAction:{scenario_id}"


    # Không tạo lại action
    # if robot_action_id in _created_robot_actions:
    #     return {
    #         "status": "skipped",
    #         "reason": "Action already executed",
    #         "robot_action_id": robot_action_id,
    #         "zone_id": zone_id
    #     }

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


    all_plugs = [
        "smart_plug_a101",
        "smart_plug_a102",
        "smart_plug_a103",
        "smart_plug_a104",
        "smart_plug_a105",
        "smart_plug_a106",
    ]
    all_alarms = [
        "audible_alarm_a101"
    ]
    isConnected = RobotClient.connect(timeout=2.0)
    # ============================================
    # THỰC THI THOẠI ROBOT KẾT HỢP IOT KHUYẾN NGHỊ
    # ============================================
    if isConnected:
        try:
            print("🎭 Robot mở biểu cảm khẩn cấp...")
            RobotClient.play_emotion("emotion://va/techface_upset")

            # Robot di chuyển tiến về phía trước 5 giây

            RobotClient.move_and_wait(distance=1.27, speed=0.45)
            RobotClient.move_and_wait(turningAngle=84.6,turningSpeed=45)

            # 1. Phát thông báo sơ tán khẩn cấp (Tiếng Anh trước, Tiếng Việt sau)
            print(f"📢 Robot phát thoại tiếng Anh (EN): \"{messageCitical}\"")
            RobotClient.speak_and_wait(messageCitical, language="en")

            print(f"📢 Robot phát thoại tiếng Việt (VI): \"{vi_messageCitical}\"")
            RobotClient.speak_and_wait(vi_messageCitical, language="vi")

            # 2. Robot thông báo ngắt điện (Tiếng Anh trước, Tiếng Việt sau) -> NGẮT ĐIỆN IOT
            print(f"📢 Robot thông báo ngắt điện (EN): \"{messageSmartPlug}\"")
            RobotClient.speak_and_wait(messageSmartPlug, language="en")

            print(f"📢 Robot thông báo ngắt điện (VI): \"{vi_messageSmartPlug}\"")
            RobotClient.speak_and_wait(vi_messageSmartPlug, language="vi")

            print(f"⚡ [CRITICAL IOT] Robot đã nói xong câu tắt thiết bị -> Đang ngắt điện {len(all_plugs)} ổ cắm Smart Plug...")
            control_multiple_by_fiware_ids(
                fiware_ids=all_plugs,
                action="off",
                device_type="smart_plug",
                max_workers=len(all_plugs)
            )

            # 3. Robot thông báo bật còi báo động (Tiếng Anh trước, Tiếng Việt sau) -> BẬT CÒI ALARM
            print(f"📢 Robot thông báo bật còi (EN): \"{messageAlarm}\"")
            RobotClient.speak_and_wait(messageAlarm, language="en")

            print(f"📢 Robot thông báo bật còi (VI): \"{vi_messageAlarm}\"")
            RobotClient.speak_and_wait(vi_messageAlarm, language="vi")

            # Bật còi báo động Alarm đã được tách sang nút điều khiển độc lập trên giao diện (btn_11A)
            print(f"🚨 [CRITICAL IOT] Robot đã nói xong câu bật còi -> Đang kích hoạt chuông còi báo động Alarm ({len(all_alarms)} thiết bị)...")
            control_multiple_by_fiware_ids(
                fiware_ids=all_alarms,
                action="on",
                device_type="alarm",
                alarm_type=8,
                duration=30,
                max_workers=len(all_alarms)
            )

            RobotClient.move_and_wait(turningAngle=175,turningSpeed=45)
            # RobotClient.move_and_wait(turningAngle=177,turningSpeed=45)

            print(f"📢 Robot thông báo di chuyển ra khỏi khu vực nguy hiểm (EN): \"{messageMoveOut}\"")
            RobotClient.speak_and_wait(messageMoveOut, language="en")

            print(f"📢 Robot thông báo di chuyển ra khỏi khu vực nguy hiểm (VI): \"{vi_messageMoveOut}\"")
            RobotClient.speak_and_wait(vi_messageMoveOut, language="vi")

            RobotClient.move_and_wait(distance=5.3, speed=0.45)
            RobotClient.move_and_wait(turningAngle=-84.6, turningSpeed=45)


        except Exception as err:
            print(f"   ⚠️ Robot execution note: {err}")
        finally:
            try:
                RobotClient.disconnect()
            except Exception:
                pass
    else:
        print("   🤖 Robot offline mode: Thực thi ngắt điện Smart Plugs và bật Còi báo động Alarm...")
        print(f"⚡ [CRITICAL IOT] Đang ngắt điện toàn bộ {len(all_plugs)} ổ cắm Smart Plug...")
        control_multiple_by_fiware_ids(
            fiware_ids=all_plugs,
            action="off",
            device_type="smart_plug",
            max_workers=len(all_plugs)
        )

        print(f"🚨 [CRITICAL IOT] Đang kích hoạt chuông còi báo động Alarm ({len(all_alarms)} thiết bị)...")
        control_multiple_by_fiware_ids(
            fiware_ids=all_alarms,
            action="on",
            device_type="alarm",
            alarm_type=10,
            duration=60,
            max_workers=len(all_alarms)
        )


    return {
        "status": "success",
        "demo_run_id": demo_run_id,
        "alert_id": alert_id,
        "scenario_id": scenario_id,
        "robot_action_id": robot_action_id,
        "zone_id": zone_id,
        "smart_plugs_turned_off": len(all_plugs),
        "alarms_activated": len(all_alarms),
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


def test_robot_connection() -> dict:
    """
    Kiểm tra trạng thái kết nối tới Robot Cruzr thật (WebSocket).
    Nếu không kết nối được (Robot Offline), tự động chuyển sang chế độ Mô Phỏng (Simulator).
    """
    try:
        robot = CruzrRobotClient()
        connected = robot.connect(timeout=2.0)
        if connected:
            robot.disconnect()
            return {
                "connected": True,
                "message": f"🤖 Đã kết nối thành công tới Robot Cruzr thật tại IP: {robot.ip}:{robot.port}"
            }
        else:
            return {
                "connected": False,
                "message": f"⚠️ Không thể kết nối tới Robot Cruzr tại IP: {robot.ip}:{robot.port}. Hệ thống chuyển sang chế độ mô phỏng Offline."
            }
    except Exception as err:
        return {
            "connected": False,
            "message": f"⚠️ Robot Cruzr đang Offline hoặc chưa mở WebSocket server ({err}). Đang dùng Simulator Offline."
        }


def run_robot_action_async(event: dict = None) -> dict:
    """
    Kích hoạt kịch bản Robot sơ tán & ngắt điện IoT bất đồng bộ trong background thread.
    Trả phản hồi về cho caller/Web UI tức thì (< 5ms).
    """
    import threading
    thread = threading.Thread(target=main, args=(event,), daemon=True)
    thread.start()
    return {
        "success": True,
        "message": "⚡ Kịch bản Robot Cruzr & Tuya IoT đã được phát đi bất đồng bộ tức thì (Non-blocking)!"
    }
