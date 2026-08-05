import os
import sys
import json
import asyncio
import concurrent.futures
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from src.tuya import control_multiple_by_fiware_ids
from src.fiware import get_smart_plugs_in_room, get_alarms_in_room
from .cruzr_client import CruzrRobotClient
from src.utils import translate_to_vietnamese, estimate_speak_duration

# Cấu hình UTF-8 cho Windows console
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Lưu các action đã thực hiện trong phiên chạy hiện tại (Idempotency Cache)
_created_robot_actions = set()


def reset_robot_action_cache():
    """Xóa cache các robot action đã thực hiện"""
    global _created_robot_actions
    _created_robot_actions.clear()


def append_jsonl(path: str, data: dict):
    """Ghi log JSONL vào file"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


def test_robot_connection() -> dict:
    """Kiểm tra thử nghiệm kết nối Robot Cruzr (Cho nút Robot Retry)"""
    client = CruzrRobotClient()
    connected = client.connect()
    if connected:
        client.disconnect()
        return {
            "connected": True,
            "status": "CONNECTED",
            "message": "Kết nối thành công tới Robot Cruzr!"
        }
    return {
        "connected": False,
        "status": "DISCONNECTED",
        "message": "Robot chưa kết nối. Đã gửi yêu cầu kết nối lại (Retry)..."
    }


async def run_in_executor(func, *args, **kwargs):
    """Hàm hỗ trợ chạy các tác vụ I/O đồng bộ (blocking) trong thread pool bất đồng bộ"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))


async def async_main(alert_event: dict) -> dict:
    """
    Luồng xử lý cảnh báo khẩn cấp bất đồng bộ (Async Pipeline)
    """
    demo_run_id = alert_event["demo_run_id"]
    alert_id = alert_event["alert_id"]
    scenario_id = alert_event["scenario_id"]
    zone_id = alert_event["zone_id"]
    severity = alert_event.get("severity", "critical")

    robot_action_id = f"RobotAction:{scenario_id}"

    # Không thực hiện lại nếu action đã được tạo trong phiên chạy
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
    # _created_robot_actions.add(robot_action_id)

    # ============================================
    # TẠO MESSAGE VÀ DỊCH SANG TIẾNG VIỆT
    # ============================================
    room_name = zone_id.split("_")[-1]

    messageCitical = (
        f"Critical indoor-environment anomaly detected in "
        f"Room {room_name}. Please follow staff guidance and move calmly to the safe waiting area"
    )
    vi_messageCitical = translate_to_vietnamese(messageCitical)

    messageSmartPlug = "Turn off all electrical devices"
    vi_messageSmartPlug = translate_to_vietnamese(messageSmartPlug)

    messageAlarm = "activate the alarm"
    vi_messageAlarm = translate_to_vietnamese(messageAlarm)

    # Khởi tạo robot client
    RobotClient = CruzrRobotClient()
    isConnected = await run_in_executor(RobotClient.connect)

    # Kết nối nếu chưa kết nối
    # if not isConnected:
    #     print("   🤖 Robot not connected. Trying to connect...")
    #     return {
    #         "status": "failed",
    #         "reason": "Robot not connected",
    #         "robot_action_id": robot_action_id,
    #         "zone_id": zone_id
    #     }

    # Ghi log RobotAction
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

    smart_plugs: List[str] = []
    alarms: List[str] = []

    try:
        # Hiển thị emotion khẩn cấp
        result = await run_in_executor(RobotClient.play_emotion, "emotion://va/techface_upset")
        print(f"   😫 Emotion result: {result}")

        # Robot di chuyển
        # await run_in_executor(RobotClient.move_forward, 1)
        # await asyncio.sleep(3)
        # await run_in_executor(RobotClient.stop)

        # ============================================
        # Speak sequence (nhiều message)
        # ============================================
        await run_in_executor(RobotClient.speak, vi_messageCitical, language="vi")
        await asyncio.sleep(12)  # Đợi message tiếng Việt kết thúc

        await run_in_executor(RobotClient.speak, messageCitical, language="en")
        await asyncio.sleep(14)  # Đợi message tiếng Anh kết thúc

        # Lấy danh sách smart plug và alarm trong phòng
        smart_plugs = await run_in_executor(get_smart_plugs_in_room, zone_id)
        alarms = await run_in_executor(get_alarms_in_room, zone_id)

        await run_in_executor(RobotClient.speak, vi_messageSmartPlug, language="vi")
        await asyncio.sleep(4)

        await run_in_executor(RobotClient.speak, messageSmartPlug, language="en")
        await asyncio.sleep(0.01)

        # Tắt Smart Plug
        if smart_plugs:
            print(f"   [IOT-PLUGS] Đang gửi lệnh tắt {len(smart_plugs)} ổ cắm điện (Smart Plugs)...")
            await run_in_executor(
                control_multiple_by_fiware_ids,
                fiware_ids=smart_plugs,
                action="off",
                device_type="smart_plug",
                max_workers=len(smart_plugs)
            )

        await run_in_executor(RobotClient.speak, vi_messageAlarm, language="vi")
        await asyncio.sleep(4)

        await run_in_executor(RobotClient.speak, messageAlarm, language="en")
        await asyncio.sleep(4)

        # Bật Alarm
        if alarms:
            print(f"   [IOT-ALARM] Đang gửi lệnh kích hoạt {len(alarms)} còi báo động (Alarms)...")
            await run_in_executor(
                control_multiple_by_fiware_ids,
                fiware_ids=alarms,
                action="on",
                device_type="alarm",
                alarm_type=10,
                duration=60,
                max_workers=len(alarms)
            )
    finally:
        if RobotClient and RobotClient.is_connected():
            await run_in_executor(RobotClient.disconnect)

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


def main(alert_event: dict) -> dict:
    """
    Hàm wrapper đồng bộ (Synchronous Wrapper) tương thích 100% với các test suite và pipeline đồng bộ.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(lambda: asyncio.run(async_main(alert_event))).result()
    else:
        return asyncio.run(async_main(alert_event))


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

