"""
Hệ thống điều khiển Robot Cruzr & IoT tự động khẩn cấp (Asynchronous Cluster Pipeline)
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List

# Cấu hình UTF-8 cho Windows console để tránh lỗi UnicodeEncodeError
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from src.tuya import control_multiple_by_fiware_ids
from src.fiware import get_smart_plugs_in_room, get_alarms_in_room
from src.robot.cruzr_client import CruzrRobotClient
from src.utils import translate_to_vietnamese, estimate_speak_duration


# Lưu các action đã thực hiện trong phiên chạy hiện tại (Idempotency Cache)
_created_robot_actions = set()


def append_jsonl(path: str, data: dict):
    """Ghi log JSONL vào file"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


def get_utc_timestamp() -> str:
    """Trả về timestamp ISO8601 UTC chuẩn"""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


async def run_in_executor(func, *args, **kwargs):
    """Hàm hỗ trợ chạy các tác vụ I/O đồng bộ (blocking) trong thread pool bất đồng bộ"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))


async def async_speak_sequence(robot_client: CruzrRobotClient, message: str, language: str) -> bool:
    """
    Gửi lệnh nói và chờ chính xác theo thời gian ước lượng nói (không chồng chéo lệnh)
    """
    if not robot_client or not robot_client.is_connected():
        print(f"   [WARNING] [Speak {language.upper()}] Bỏ qua do robot chưa kết nối: {message[:40]}...")
        return False

    duration = estimate_speak_duration(message, language=language) + 1.5  # Thêm 1.5s buffer an toàn cho TTS engine
    print(f"   [SPEAK - {language.upper()}] (đợi ~{duration:.1f}s): {message[:50]}...")
    
    # Gửi lệnh nói sang WebSocket (chạy in executor để không block loop)
    await run_in_executor(robot_client.speak, message, language=language)
    
    # Ngủ bất đồng bộ để chờ robot nói xong hoàn toàn trước khi lệnh tiếp theo được gửi
    await asyncio.sleep(duration)
    return True


async def async_main(alert_event: dict) -> dict:
    """
    Luồng xử lý cảnh báo khẩn cấp chia cụm (Clustering Pipeline) bất đồng bộ
    """
    demo_run_id = alert_event["demo_run_id"]
    alert_id = alert_event["alert_id"]
    scenario_id = alert_event["scenario_id"]
    zone_id = alert_event["zone_id"]
    severity = alert_event.get("severity", "critical")

    robot_action_id = f"RobotAction:{scenario_id}"

    # Kiểm tra Idempotency: Không thực hiện lại nếu action đã tạo trong phiên chạy
    if robot_action_id in _created_robot_actions:
        return {
            "status": "skipped",
            "reason": "Action already executed",
            "robot_action_id": robot_action_id,
            "zone_id": zone_id
        }

    # Chỉ xử lý cảnh báo mức độ critical
    if severity.lower() != "critical":
        return {
            "status": "skipped",
            "reason": f"severity={severity}",
            "zone_id": zone_id
        }

    # Đánh dấu đã xử lý
    _created_robot_actions.add(robot_action_id)

    room_name = zone_id.split("_")[-1]
    
    # Chuẩn bị nội dung thông báo
    msg_critical_en = (
        f"Critical indoor-environment anomaly detected in Room {room_name}. "
        f"Please follow staff guidance and move calmly to the safe waiting area. "
    )
    msg_critical_vi = translate_to_vietnamese(msg_critical_en)

    msg_plugs_en = "Turn off all electrical devices."
    msg_plugs_vi = translate_to_vietnamese(msg_plugs_en)

    msg_alarm_en = "activate the alarm.."
    msg_alarm_vi = translate_to_vietnamese(msg_alarm_en)

    # Ghi log RobotAction PENDING
    log_entry = {
        "demo_run_id": demo_run_id,
        "timestamp": get_utc_timestamp(),
        "robot_id": "CRUZR_01",
        "alert_id": alert_id,
        "zone_id": zone_id,
        "action_type": "VOICE_DISPLAY_GUIDANCE",
        "navigation_mode": "PREDEFINED_RESPONSE_POINT",
        "message": msg_critical_en,
        "status": "PENDING"
    }
    log_path = ROOT_DIR / "logs" / "robot_actions.jsonl"
    append_jsonl(str(log_path), log_entry)

    # Khởi tạo Robot Client
    robot_client = CruzrRobotClient()
    smart_plugs: List[str] = []
    alarms: List[str] = []

    try:
        # ============================================================
        # [CLUSTER 1] ROBOT CONNECT & EMOTION (Kết nối & Cảm xúc khẩn cấp)
        # ============================================================
        print("\n" + "="*60)
        print("[CLUSTER 1] ROBOT CONNECT & EMOTION (Kết nối & Cảm xúc)")
        print("="*60)
        
        is_connected = await run_in_executor(robot_client.connect)
        if not is_connected:
            print("   [WARNING] Không thể kết nối với Robot Cruzr thật. Tiếp tục xử lý các lệnh IoT (Plugs/Alarm)...")
        else:
            print("   [SUCCESS] Kết nối Robot thành công! Đang hiển thị Emotion khẩn cấp...")
            res_emotion = await run_in_executor(robot_client.play_emotion, "emotion://va/techface_upset")
            print(f"   [EMOTION] Result: {res_emotion}")
            # Đợi 2.5s để activity hiển thị Emotion trên Android Cruzr tải xong, tránh xung đột lệnh Voice
            await asyncio.sleep(2.5)

        # ============================================================
        # [CLUSTER 2] VOICE & DISPLAY GUIDANCE (Cảnh báo sơ tán)
        # ============================================================
        print("\n" + "="*60)
        print("[CLUSTER 2] VOICE & DISPLAY GUIDANCE (Cảnh báo sơ tán khẩn cấp)")
        print("="*60)
        
        await async_speak_sequence(robot_client, msg_critical_vi, "vi")
        await async_speak_sequence(robot_client, msg_critical_en, "en")

        # ============================================================
        # [CLUSTER 3] ELECTRICAL ACTUATION (Tắt toàn bộ ổ cắm điện)
        # ============================================================
        print("\n" + "="*60)
        print("[CLUSTER 3] ELECTRICAL ACTUATION (Tắt thiết bị điện & Lời nhắc)")
        print("="*60)
        
        # Lấy danh sách smart plugs trong phòng
        smart_plugs = await run_in_executor(get_smart_plugs_in_room, zone_id)
        print(f"   [INFO] Tìm thấy {len(smart_plugs)} ổ cắm điện trong phòng {zone_id}.")
        
        # Nói lời nhắc tắt điện
        await async_speak_sequence(robot_client, msg_plugs_vi, "vi")
        await async_speak_sequence(robot_client, msg_plugs_en, "en")
        
        if smart_plugs:
            print(f"   [IOT-PLUGS] Đang gửi lệnh tắt {len(smart_plugs)} ổ cắm điện (Smart Plugs)...")
            await run_in_executor(
                control_multiple_by_fiware_ids,
                fiware_ids=smart_plugs,
                action="off",
                device_type="smart_plug",
                max_workers=len(smart_plugs)
            )

        # ============================================================
        # [CLUSTER 4] ALARM & SIREN ACTUATION (Kích hoạt còi báo động)
        # ============================================================
        print("\n" + "="*60)
        print("[CLUSTER 4] ALARM & SIREN ACTUATION (Kích hoạt còi báo động)")
        print("="*60)
        
        # Lấy danh sách alarm trong phòng
        alarms = await run_in_executor(get_alarms_in_room, zone_id)
        print(f"   [INFO] Tìm thấy {len(alarms)} thiết bị cảnh báo trong phòng {zone_id}.")
        
        # Nói lời nhắc bật còi
        await async_speak_sequence(robot_client, msg_alarm_vi, "vi")
        await async_speak_sequence(robot_client, msg_alarm_en, "en")
        
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
        # ============================================================
        # [CLUSTER 5] SAFE DISCONNECT & CLEANUP (Ngắt kết nối an toàn)
        # ============================================================
        print("\n" + "="*60)
        print("[CLUSTER 5] SAFE DISCONNECT & CLEANUP (Ngắt kết nối an toàn)")
        print("="*60)
        if robot_client and robot_client.is_connected():
            print("   [CLEANUP] Đang ngắt kết nối WebSocket an toàn với Robot Cruzr...")
            await run_in_executor(robot_client.disconnect)
            print("   [SUCCESS] Đã đóng socket thành công. Đảm bảo Robot không bị reset/nháy màn hình.")
        else:
            print("   [INFO] Robot không trong trạng thái kết nối cần đóng.")
        print("="*60 + "\n")

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
    Hàm wrapper đồng bộ (Synchronous Wrapper) để tương thích 100% với các test suite và alert_service hiện tại.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Nếu đang trong event loop có sẵn (vd: Jupyter hoặc test runner), chạy qua ThreadPoolExecutor
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(lambda: asyncio.run(async_main(alert_event))).result()
    else:
        # Khởi tạo event loop mới
        return asyncio.run(async_main(alert_event))


if __name__ == "__main__":
    test_event = {
        "demo_run_id": "DNTU02_TOP8_RUN_2026_001",
        "alert_id": "AlertEvent:SCN_CRITICAL_001",
        "scenario_id": "critical_001",
        "zone_id": "DNTU_ROOM_A101",
        "severity": "critical"
    }

    res = main(test_event)
    print(json.dumps(res, indent=2, ensure_ascii=False))
