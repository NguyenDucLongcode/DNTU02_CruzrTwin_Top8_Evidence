"""
src/fiware/script_runner_api.py
===================================================
Flask Blueprint & Handler xử lý kích chạy các script Python, kịch bản mô phỏng,
điều khiển IoT Tuya, phát thoại Robot Cruzr từ giao diện Remote Controller NavigateBack.
===================================================
"""

import os
import sys
import time
import subprocess
import threading
from typing import Dict, Any
from flask import Blueprint, request, jsonify

# Đảm bảo console Windows luôn in emoji và tiếng Việt bằng mã hóa UTF-8 an toàn
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Khai báo Flask Blueprint cho Controller Script Runner
script_runner_bp = Blueprint('script_runner', __name__)

GLOBAL_CONTROLLER_STATE = {
    "ai_detection_focus": False
}

# Registry chứa cấu hình 12 nút bấm (Sẵn sàng cập nhật tính năng từng nút khi User mô tả)
BUTTON_SLOTS: Dict[str, Dict[str, Any]] = {
    "btn_1": {
        "id": "btn_1",
        "name": "Phát Thoại Giới Thiệu",
        "desc": "Robot Cruzr chào & phát thoại giới thiệu",
        "script": "src/robot/speak_intro.py"
    },
    "btn_2": {
        "id": "btn_2",
        "name": "Focus Log AI Detection",
        "desc": "Bật/Tắt hiển thị Zoom AI Detection trên Dashboard",
        "type": "toggle"
    },
    "btn_3": {
        "id": "btn_3",
        "name": "Kịch Bản Normal",
        "desc": "Kích hoạt dữ liệu Normal & Khôi phục thiết bị IoT",
        "scenario": "normal"
    },
    "btn_4": {
        "id": "btn_4",
        "name": "Kịch Bản Warning",
        "desc": "Kích hoạt cảnh báo mức độ Warning (Nhiệt độ/CO2)",
        "scenario": "warning"
    },
    "btn_5": {
        "id": "btn_5",
        "name": "1. Phát Dữ Liệu Critical",
        "desc": "Phát log Báo Động Đỏ Critical (Cháy/Khói) & chưa kích hoạt Robot",
        "scenario": "critical_log_only"
    },
    "btn_6": {
        "id": "btn_6",
        "name": "2. Kích Hoạt Robot & IoT",
        "desc": "Gọi Robot Cruzr phát thoại sơ tán & ngắt điện Tuya IoT",
        "scenario": "robot_dispatch"
    },
    "btn_7": {
        "id": "btn_7",
        "name": "Phát Thoại Outro (Cảm Ơn)",
        "desc": "Robot Cruzr chào cảm ơn & phát thoại kết thúc phần thi (src/robot/speak_outro.py)",
        "script": "src/robot/speak_outro.py"
    },
    "btn_8": {
        "id": "btn_8",
        "name": "Dừng Di Chuyển Robot",
        "desc": "Ngắt di chuyển bánh xe Robot ngay lập tức (Vẫn giữ thoại, log & IoT)",
        "scenario": "stop_movement"
    },
    "btn_9": {
        "id": "btn_9",
        "name": "Reset Demo System",
        "desc": "Reset toàn bộ trạng thái Demo: Xóa cache, bật lại điện Tuya Smart Plugs & tắt còi Alarm",
        "scenario": "reset_all"
    },
    "btn_10": {
        "id": "btn_10",
        "name": "Khôi Phục Điện Tuya Plugs (ON)",
        "desc": "Bật toàn bộ ổ cắm thông minh Tuya Smart Plugs (scripts/tools/control_iot/control_all_smart_plugs.py on)",
        "script": "scripts/tools/control_iot/control_all_smart_plugs.py",
        "args": ["on"]
    },
    "btn_11": {
        "id": "btn_11",
        "name": "Ngắt Điện Tuya Plugs (OFF)",
        "desc": "Tắt toàn bộ ổ cắm thông minh Tuya Smart Plugs (scripts/tools/control_iot/control_all_smart_plugs.py off)",
        "script": "scripts/tools/control_iot/control_all_smart_plugs.py",
        "args": ["off"]
    },
    "btn_12": {
        "id": "btn_12",
        "name": "Test Kết Nối Robot",
        "desc": "Kiểm tra trạng thái ping & kết nối tới Robot Cruzr",
        "scenario": "robot_retry"
    },
}


def run_python_script_async(script_relative_path: str, args: list = None) -> None:
    """Chạy một file Python trong background thread không làm block Flask server"""
    def _target():
        try:
            full_path = os.path.join(ROOT_DIR, script_relative_path)
            cmd = [sys.executable, full_path] + (args or [])
            print(f"🚀 [SCRIPT RUNNER] Đang chạy script: {' '.join(cmd)}")
            res = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if res.returncode == 0:
                print(f"✅ [SCRIPT RUNNER] Thành công: {script_relative_path}")
            else:
                print(f"❌ [SCRIPT RUNNER] Lỗi khi chạy {script_relative_path}: {res.stderr}")
        except Exception as err:
            print(f"❌ [SCRIPT RUNNER] Exception: {err}")

    threading.Thread(target=_target, daemon=True).start()


def run_scenario_replay(scenario_type: str) -> dict:
    """Hàm phát lại kịch bản replay test set (normal, warning, critical) tương tự như Dashboard"""
    file_map = {
        "normal": "normal_001.json",
        "warning": "warning_001.json",
        "critical": "critical_001.json"
    }

    target_file = file_map.get(scenario_type)
    if not target_file:
        return {"success": False, "error": f"Invalid scenario type: {scenario_type}"}

    file_path = os.path.join(ROOT_DIR, "data", "replay_test_set", target_file)
    if not os.path.exists(file_path):
        return {"success": False, "error": f"File kịch bản không tồn tại: {file_path}"}

    try:
        from pathlib import Path
        from src.utils.replay_helpers import load_test_file, extract_all_readings, extract_device_values_from_reading, build_scenario_id
        from src.orchestration.pipeline import process_sensor_event

        test_data = load_test_file(Path(file_path))
        readings = extract_all_readings(test_data)
        scenario_id = build_scenario_id(target_file)

        generated_count = 0
        for reading in readings:
            device_values = extract_device_values_from_reading(reading)
            payload = {
                "scenario_id": scenario_id,
                "temperature": device_values.get("temp_sensor_a101", 25.0),
                "humidity": device_values.get("humid_sensor_a101", 60.0),
                "smoke": device_values.get("smoke_sensor_a101", 0.0),
                "co2": device_values.get("air_sensor_a101", 400.0),
                "power": device_values.get("energy_sensor_e101", 50.0)
            }
            process_sensor_event(payload)
            generated_count += 1

        if scenario_type == "normal":
            try:
                from src.fiware.webhook_receiver import restore_tuya_devices
                threading.Thread(target=restore_tuya_devices, daemon=True).start()
            except Exception:
                pass

        return {
            "success": True,
            "message": f"🚀 Kịch bản {scenario_type.upper()} thực thi thành công! Đã tạo {generated_count} bản ghi log.",
            "generated_logs": generated_count
        }
    except Exception as err:
        return {"success": False, "error": str(err)}


def run_critical_scenario_logs_only() -> dict:
    """Tạo dữ liệu Critical replay log mà không kích hoạt Robot Cruzr ngay lập tức (Dành cho Slot 05)"""
    file_path = os.path.join(ROOT_DIR, "data", "replay_test_set", "critical_001.json")
    if not os.path.exists(file_path):
        return {"success": False, "error": f"File kịch bản không tồn tại: {file_path}"}

    try:
        from pathlib import Path
        from src.utils.replay_helpers import load_test_file, extract_all_readings, extract_device_values_from_reading, build_scenario_id
        from src.orchestration.pipeline import process_sensor_event
        from src.alerts import alert_service

        # Xóa cache robot action để chuẩn bị cho Slot 06 kích hoạt
        alert_service._created_robot_actions.clear()

        test_data = load_test_file(Path(file_path))
        readings = extract_all_readings(test_data)
        scenario_id = build_scenario_id("critical_001.json")

        generated_count = 0
        for reading in readings:
            device_values = extract_device_values_from_reading(reading)
            payload = {
                "scenario_id": scenario_id,
                "temperature": device_values.get("temp_sensor_a101", 68.5),
                "humidity": device_values.get("humid_sensor_a101", 32.4),
                "smoke": device_values.get("smoke_sensor_a101", 1.0),
                "co2": device_values.get("air_sensor_a101", 2850.0),
                "power": device_values.get("energy_sensor_e101", 1450.0),
                "skip_robot_dispatch": True
            }
            process_sensor_event(payload)
            generated_count += 1

        return {
            "success": True,
            "message": f"🚨 [BƯỚC 1] Đã phát dữ liệu Critical! Màn hình 3D/Logs đã báo động đỏ. Sẵn sàng ấn Slot 06 để gọi Robot."
        }
    except Exception as err:
        return {"success": False, "error": str(err)}


def dispatch_robot_emergency_action_async() -> dict:
    """Kích hoạt Robot Cruzr & Tuya IoT khẩn cấp (Dành cho Slot 06)"""
    def _target():
        try:
            from src.robot.create_robot_action import main as create_robot_action_main
            event = {
                "demo_run_id": "DNTU02_TOP8_RUN_2026_001",
                "alert_id": "AlertEvent:SCN_CRITICAL_001",
                "scenario_id": "critical_001",
                "zone_id": "DNTU_ROOM_A101",
                "severity": "critical"
            }
            print("🤖 [SLOT 06] Đang kích hoạt Robot Cruzr & Khống chế IoT...")
            create_robot_action_main(event)
        except Exception as err:
            print(f"❌ [SLOT 06] Lỗi Robot action: {err}")

    threading.Thread(target=_target, daemon=True).start()
    return {
        "success": True,
        "message": "🚀 Đã kích hoạt Robot Cruzr di chuyển & khống chế IoT khẩn cấp trong background!"
    }

def test_robot_connection_action() -> dict:
    """Kiểm tra trạng thái kết nối tới Robot Cruzr thật qua WebSocket (Dành cho Slot 12 / Nút 16)"""
    try:
        from src.robot.create_robot_action import test_robot_connection
        res = test_robot_connection()
        return {
            "success": True,
            "connected": res.get("connected", False),
            "message": res.get("message", "Đã kiểm tra kết nối Robot thành công!")
        }
    except Exception as err:
        return {
            "success": False,
            "connected": False,
            "message": f"❌ Lỗi khi kiểm tra kết nối Robot Cruzr: {err}"
        }


def stop_robot_movement_action() -> dict:
    """Nút 08: Đảo trạng thái dừng / tiếp tục di chuyển bánh xe Robot (Toggle Movement Pause/Resume)"""
    try:
        from src.robot.cruzr_client import CruzrRobotClient, toggle_global_movement_stopped
        # 1. Đảo cờ dừng di chuyển toàn cục (True <-> False)
        is_stopped = toggle_global_movement_stopped()

        # 2. Nếu vừa đổi sang Tạm Dừng, gửi lệnh ngắt di chuyển tới Robot lập tức
        if is_stopped:
            client = CruzrRobotClient()
            if client.connect(timeout=1.0):
                client.stop_move()
                client.disconnect()
            msg = "🛑 Đã DỪNG di chuyển bánh xe Robot! (Ấn lại Nút 8 để TIẾP TỤC di chuyển)."
        else:
            msg = "▶️ Đã TIẾP TỤC cho phép Robot di chuyển!"

        return {
            "success": True,
            "is_stopped": is_stopped,
            "message": msg
        }
    except Exception as err:
        return {"success": False, "error": str(err)}


def reset_demo_action() -> dict:
    """Reset toàn bộ hệ thống Demo: xóa sạch 8 file logs, reset cache, khôi phục điện Tuya Plugs ON, tắt còi Alarm OFF"""
    try:
        from src.alerts.alert_service import reset_alert_service_cache
        from src.robot.create_robot_action import reset_robot_action_cache
        from src.robot.cruzr_client import set_global_movement_stopped
        reset_alert_service_cache()
        reset_robot_action_cache()
        set_global_movement_stopped(False)

        log_files = [
            "sensorReading.jsonl",
            "sensor_readings.jsonl",
            "orion_state.jsonl",
            "ai_detection.jsonl",
            "alert_events.jsonl",
            "robot_actions.jsonl",
            "operator_ack.jsonl",
            "operator_acks.jsonl"
        ]
        logs_dir = os.path.join(ROOT_DIR, "logs")
        for filename in log_files:
            filepath = os.path.join(logs_dir, filename)
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception as e:
                    print(f"Error deleting log file {filename}: {e}")

        def _restore_bg():
            try:
                from src.tuya import control_multiple_by_fiware_ids
                all_plugs = ["smart_plug_a101", "smart_plug_a102", "smart_plug_a103", "smart_plug_a104", "smart_plug_a105", "smart_plug_a106"]
                all_alarms = ["audible_alarm_a101"]
                print(f"🔌 [RESET DEMO] Đang bật lại toàn bộ điện {len(all_plugs)} ổ cắm Tuya...")
                control_multiple_by_fiware_ids(all_plugs, action="on", device_type="smart_plug", max_workers=len(all_plugs))
                print(f"🔕 [RESET DEMO] Đang tắt toàn bộ {len(all_alarms)} còi báo động Alarm...")
                control_multiple_by_fiware_ids(all_alarms, action="off", device_type="alarm", max_workers=len(all_alarms))
            except Exception as err:
                print(f"Reset Tuya note: {err}")

        threading.Thread(target=_restore_bg, daemon=True).start()
        return {
            "success": True,
            "message": "💥 Reset All System: Đã xóa sạch toàn bộ logs, reset cache & khôi phục điện 6 ổ cắm Tuya Plugs ON, tắt còi Alarm OFF!"
        }
    except Exception as err:
        return {"success": False, "error": str(err)}


EXECUTION_LOGS = []

def log_execution_event(btn_id: str, name: str, status: str, details: str):
    import time
    entry = {
        "timestamp": time.strftime("%H:%M:%S"),
        "button_id": btn_id,
        "name": name,
        "status": status,
        "details": details
    }
    EXECUTION_LOGS.append(entry)
    if len(EXECUTION_LOGS) > 30:
        EXECUTION_LOGS.pop(0)


def execute_button_action(button_id: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Hàm xử lý chính khi người dùng click vào 1 trong 12 nút từ giao diện Controller
    """
    # Chuẩn hóa Alias nút bấm tương thích (btn_14 -> btn_10, btn_15 -> btn_11, btn_16 -> btn_12)
    alias_map = {
        "btn_14": "btn_10",
        "btn_15": "btn_11",
        "btn_16": "btn_12"
    }
    button_id = alias_map.get(button_id, button_id)
    slot_info = BUTTON_SLOTS.get(button_id)
    if not slot_info:
        res = {
            "success": False,
            "error": f"Nút '{button_id}' không hợp lệ. Danh sách chấp nhận: btn_1 -> btn_12"
        }
        log_execution_event(button_id, "Unknown", "FAILED", res["error"])
        return res

    # Nếu không phải nút Slot 02 (Focus AI Detection), tự động tắt Focus Mode trên Dashboard để trả lại độ sáng thường
    if button_id != "btn_2":
        GLOBAL_CONTROLLER_STATE["ai_detection_focus"] = False

    # Slot 01: Kích hoạt thoại giới thiệu Robot Cruzr
    if button_id == "btn_1":
        run_python_script_async("src/robot/speak_intro.py")
        msg = "🚀 Đã kích hoạt chạy script Robot Giới Thiệu (src/robot/speak_intro.py)!"
        log_execution_event(button_id, slot_info["name"], "SUCCESS 200 OK", msg)
        return {
            "success": True,
            "button_id": button_id,
            "name": slot_info["name"],
            "desc": slot_info["desc"],
            "message": msg
        }

    # Slot 02: Toggle Modal Focus AI Detection Log trên Dashboard
    if button_id == "btn_2":
        GLOBAL_CONTROLLER_STATE["ai_detection_focus"] = not GLOBAL_CONTROLLER_STATE["ai_detection_focus"]
        is_on = GLOBAL_CONTROLLER_STATE["ai_detection_focus"]
        status_text = "ĐÃ BẬT Focus AI Detection Panel trên Dashboard!" if is_on else "ĐÃ TẮT Focus AI Detection Panel (Trở về giao diện thường)!"
        msg = f"👁️ [{status_text}]"
        log_execution_event(button_id, slot_info["name"], "TOGGLE 200 OK", msg)
        return {
            "success": True,
            "button_id": button_id,
            "name": slot_info["name"],
            "desc": slot_info["desc"],
            "active": is_on,
            "message": msg
        }

    # Slot 03: Kịch bản NORMAL (Replay Normal & Khôi phục IoT)
    if button_id == "btn_3":
        res = run_scenario_replay("normal")
        msg = res.get("message", "Thực thi kịch bản Normal thành công!")
        log_execution_event(button_id, slot_info["name"], "SUCCESS 200 OK", msg)
        return {
            "success": True,
            "button_id": button_id,
            "name": slot_info["name"],
            "desc": slot_info["desc"],
            "message": msg
        }

    # Slot 04: Kịch bản WARNING (Replay Warning - Nhiệt độ/CO2 tăng)
    if button_id == "btn_4":
        res = run_scenario_replay("warning")
        msg = res.get("message", "Thực thi kịch bản Warning thành công!")
        log_execution_event(button_id, slot_info["name"], "SUCCESS 200 OK", msg)
        return {
            "success": True,
            "button_id": button_id,
            "name": slot_info["name"],
            "desc": slot_info["desc"],
            "message": msg
        }

    # Slot 05: Kịch bản CRITICAL BƯỚC 1 (Chỉ phát dữ liệu Log Báo Động Đỏ)
    if button_id == "btn_5":
        res = run_critical_scenario_logs_only()
        msg = res.get("message", "Đã phát dữ liệu Critical Log thành công!")
        log_execution_event(button_id, slot_info["name"], "SUCCESS 200 OK", msg)
        return {
            "success": True,
            "button_id": button_id,
            "name": slot_info["name"],
            "desc": slot_info["desc"],
            "message": msg
        }

    # Slot 06: Kịch bản CRITICAL BƯỚC 2 (Kích hoạt Robot Cruzr & IoT Khẩn Cấp)
    if button_id == "btn_6":
        res = dispatch_robot_emergency_action_async()
        msg = res.get("message", "Đã gửi lệnh kích hoạt Robot & IoT khẩn cấp!")
        log_execution_event(button_id, slot_info["name"], "SUCCESS 200 OK", msg)
        return {
            "success": True,
            "button_id": button_id,
            "name": slot_info["name"],
            "desc": slot_info["desc"],
            "message": msg
        }

    # Slot 07: Kích hoạt thoại Outro cảm ơn Robot Cruzr
    if button_id == "btn_7":
        run_python_script_async("src/robot/speak_outro.py")
        msg = "🚀 Đã kích hoạt script Robot Outro Cảm Ơn (src/robot/speak_outro.py)!"
        log_execution_event(button_id, slot_info["name"], "SUCCESS 200 OK", msg)
        return {
            "success": True,
            "button_id": button_id,
            "name": slot_info["name"],
            "desc": slot_info["desc"],
            "message": msg
        }

    # Slot 08: Dừng di chuyển bánh xe Robot ngay lập tức (Giữ nguyên âm thanh, thoại & IoT)
    if button_id == "btn_8":
        res = stop_robot_movement_action()
        msg = res.get("message", "Đã gửi lệnh dừng di chuyển bánh xe Robot!")
        log_execution_event(button_id, slot_info["name"], "SUCCESS 200 OK", msg)
        return {
            "success": True,
            "button_id": button_id,
            "name": slot_info["name"],
            "desc": slot_info["desc"],
            "message": msg
        }

    # Slot 09: Reset Demo (Ấn 1 lần = Undo log gần nhất | Ấn 3 lần = Reset All System)
    if button_id == "btn_9":
        sub_action = (payload or {}).get("action") or (payload or {}).get("scenario") or "reset_all"
        if sub_action == "undo":
            try:
                from src.fiware.webhook_receiver import remove_last_log_line
                remove_last_log_line()
                msg = "↩️ Undo: Đã xóa 1 dòng log vừa thực hiện gần nhất khỏi hệ thống!"
            except Exception as e:
                msg = f"↩️ Undo log note: {e}"
        else:
            res = reset_demo_action()
            msg = res.get("message", "Đã Reset toàn bộ trạng thái Demo thành công!")

        log_execution_event(button_id, slot_info["name"], "SUCCESS 200 OK", msg)
        return {
            "success": True,
            "button_id": button_id,
            "name": slot_info["name"],
            "desc": slot_info["desc"],
            "message": msg
        }

    # Slot 10 (Nút 14): Bật toàn bộ ổ cắm thông minh Tuya Smart Plugs (ON)
    if button_id in ["btn_10", "btn_14"]:
        run_python_script_async("scripts/tools/control_iot/control_all_smart_plugs.py", ["on"])
        msg = "💡 Đã kích hoạt script bật điện toàn bộ Tuya Smart Plugs (py scripts/tools/control_iot/control_all_smart_plugs.py on)!"
        log_execution_event(button_id, slot_info.get("name", "Khôi Phục Điện Tuya Plugs"), "SUCCESS 200 OK", msg)
        return {
            "success": True,
            "button_id": button_id,
            "name": slot_info.get("name", "Khôi Phục Điện Tuya Plugs"),
            "desc": slot_info.get("desc", "Bật toàn bộ ổ cắm Tuya Smart Plugs"),
            "message": msg
        }

    # Slot 11 (Nút 15): Tắt toàn bộ ổ cắm thông minh Tuya Smart Plugs (OFF)
    if button_id in ["btn_11", "btn_15"]:
        run_python_script_async("scripts/tools/control_iot/control_all_smart_plugs.py", ["off"])
        msg = "⚡ Đã kích hoạt script ngắt điện toàn bộ Tuya Smart Plugs (py scripts/tools/control_iot/control_all_smart_plugs.py off)!"
        log_execution_event(button_id, slot_info.get("name", "Ngắt Điện Tuya Plugs"), "SUCCESS 200 OK", msg)
        return {
            "success": True,
            "button_id": button_id,
            "name": slot_info.get("name", "Ngắt Điện Tuya Plugs"),
            "desc": slot_info.get("desc", "Tắt toàn bộ ổ cắm Tuya Smart Plugs"),
            "message": msg
        }

    # Slot 12 (Nút 16 hoặc btn_7 alias): Test kết nối Robot (Robot Retry / Ping Test)
    if button_id in ["btn_12", "btn_16"]:
        res = test_robot_connection_action()
        msg = res.get("message", "Đã kiểm tra kết nối Robot thành công!")
        log_execution_event(button_id, slot_info.get("name", "Test Kết Nối Robot"), "SUCCESS 200 OK" if res.get("success") else "NOTICE", msg)
        return {
            "success": True,
            "button_id": button_id,
            "name": slot_info.get("name", "Test Kết Nối Robot"),
            "desc": slot_info.get("desc", "Kiểm tra trạng thái ping & kết nối tới Robot Cruzr"),
            "connected": res.get("connected", False),
            "message": msg
        }

    msg = f"Khởi chạy nút '{button_id}' thành công! (Sẵn sàng gán tính năng chi tiết)"
    log_execution_event(button_id, slot_info["name"], "SUCCESS 200 OK", msg)
    return {
        "success": True,
        "button_id": button_id,
        "name": slot_info["name"],
        "desc": slot_info["desc"],
        "message": msg
    }


@script_runner_bp.route('/api/script/run', methods=['POST'])
def run_script_button():
    """Route tiếp nhận lệnh kích hoạt 12 nút bấm từ màn hình Remote Controller NavigateBack"""
    req_data = request.get_json(silent=True) or {}
    button_id = req_data.get("button_id", "btn_1")
    try:
        res = execute_button_action(button_id, req_data)
        status_code = 200 if res.get("success") else 400
        return jsonify(res), status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@script_runner_bp.route('/api/system/restart', methods=['POST'])
def restart_webhook_server():
    """Tắt và chạy lại py src/fiware/webhook_receiver.py (tương đương Ctrl+C rồi py...)"""
    def _restart():
        time.sleep(0.3)
        print("\n🔄 [SERVER RESTART] Đang ngắt và khởi chạy lại py src/fiware/webhook_receiver.py...")
        script_path = os.path.join(ROOT_DIR, "src", "fiware", "webhook_receiver.py")
        os.execv(sys.executable, [sys.executable, script_path])

    threading.Thread(target=_restart, daemon=True).start()
    return jsonify({
        "success": True,
        "message": "🔄 Đã gửi lệnh Restart Webhook Server! (Đang chạy lại py src/fiware/webhook_receiver.py...)"
    }), 200


@script_runner_bp.route('/api/system/stop', methods=['POST'])
def stop_webhook_server():
    """Tắt hẳn Server Webhook Receiver (tương đương Ctrl+C ngắt tiến trình Python)"""
    def _stop():
        time.sleep(0.3)
        print("\n🔴 [SERVER STOP] Đã nhận lệnh TẮT SERVER! Đang ngắt tiến trình (Ctrl+C)...")
        os._exit(0)

    threading.Thread(target=_stop, daemon=True).start()
    return jsonify({
        "success": True,
        "message": "🔴 Đã TẮT Webhook Receiver Server thành công! (Tiến trình đã ngắt giống Ctrl+C)."
    }), 200


@script_runner_bp.route('/api/system/start', methods=['POST'])
def start_webhook_server():
    """Bật Server Webhook Receiver và bật mở cửa sổ CMD Terminal hiển thị log trực tiếp"""
    try:
        script_path = os.path.join(ROOT_DIR, "src", "fiware", "webhook_receiver.py")
        py_cmd = sys.executable
        launch_cmd = f'start "CruzrTwin Webhook Receiver" cmd.exe /k ""{py_cmd}" "{script_path}""'
        print(f"\n🖥️ [SERVER START] Đang mở cửa sổ CMD Terminal: {launch_cmd}")
        subprocess.Popen(launch_cmd, shell=True, cwd=ROOT_DIR)
        return jsonify({
            "success": True,
            "message": "🖥️ Đã mở cửa sổ Terminal CMD mới và khởi chạy Webhook Receiver thành công!"
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@script_runner_bp.route('/api/script/history', methods=['GET'])
def get_script_history():
    """Route lấy lịch sử 30 lệnh vừa gửi thành công"""
    return jsonify({
        "success": True,
        "history": list(reversed(EXECUTION_LOGS))
    }), 200


@script_runner_bp.route('/api/script/state', methods=['GET'])
def get_script_state():
    """Route đọc trạng thái bật/tắt toàn cục từ Remote Controller"""
    return jsonify({
        "success": True,
        "state": GLOBAL_CONTROLLER_STATE
    }), 200
