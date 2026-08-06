"""
src/fiware/script_runner_api.py
===================================================
Flask Blueprint & Handler xử lý kích chạy các script Python, kịch bản mô phỏng,
điều khiển IoT Tuya, phát thoại Robot Cruzr từ giao diện Remote Controller NavigateBack.
===================================================
"""

import os
import sys
import subprocess
import threading
from typing import Dict, Any
from flask import Blueprint, request, jsonify

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Khai báo Flask Blueprint cho Controller Script Runner
script_runner_bp = Blueprint('script_runner', __name__)

# Registry chứa cấu hình 12 nút bấm (Sẵn sàng cập nhật tính năng từng nút khi User mô tả)
BUTTON_SLOTS: Dict[str, Dict[str, Any]] = {
    "btn_1": {"id": "btn_1", "name": "Kịch bản 1", "desc": "Chưa gán tính năng", "type": "script"},
    "btn_2": {"id": "btn_2", "name": "Kịch bản 2", "desc": "Chưa gán tính năng", "type": "script"},
    "btn_3": {"id": "btn_3", "name": "Kịch bản 3", "desc": "Chưa gán tính năng", "type": "script"},
    "btn_4": {"id": "btn_4", "name": "Kịch bản 4", "desc": "Chưa gán tính năng", "type": "script"},
    "btn_5": {"id": "btn_5", "name": "Kịch bản 5", "desc": "Chưa gán tính năng", "type": "script"},
    "btn_6": {"id": "btn_6", "name": "Kịch bản 6", "desc": "Chưa gán tính năng", "type": "script"},
    "btn_7": {"id": "btn_7", "name": "Kịch bản 7", "desc": "Chưa gán tính năng", "type": "script"},
    "btn_8": {"id": "btn_8", "name": "Kịch bản 8", "desc": "Chưa gán tính năng", "type": "script"},
    "btn_9": {"id": "btn_9", "name": "Kịch bản 9", "desc": "Chưa gán tính năng", "type": "script"},
    "btn_10": {"id": "btn_10", "name": "Kịch bản 10", "desc": "Chưa gán tính năng", "type": "script"},
    "btn_11": {"id": "btn_11", "name": "Kịch bản 11", "desc": "Chưa gán tính năng", "type": "script"},
    "btn_12": {"id": "btn_12", "name": "Kịch bản 12", "desc": "Chưa gán tính năng", "type": "script"},
}


def run_python_script_async(script_relative_path: str, args: list = None) -> None:
    """Chạy một file Python trong background thread không làm block Flask server"""
    def _target():
        try:
            full_path = os.path.join(ROOT_DIR, script_relative_path)
            cmd = [sys.executable, full_path] + (args or [])
            print(f"🚀 [SCRIPT RUNNER] Đang chạy script: {' '.join(cmd)}")
            res = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, text=True)
            if res.returncode == 0:
                print(f"✅ [SCRIPT RUNNER] Thành công: {script_relative_path}")
            else:
                print(f"❌ [SCRIPT RUNNER] Lỗi khi chạy {script_relative_path}: {res.stderr}")
        except Exception as err:
            print(f"❌ [SCRIPT RUNNER] Exception: {err}")

    threading.Thread(target=_target, daemon=True).start()


def execute_button_action(button_id: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Hàm xử lý chính khi người dùng click vào 1 trong 12 nút từ giao diện Controller
    """
    slot_info = BUTTON_SLOTS.get(button_id)
    if not slot_info:
        return {
            "success": False,
            "error": f"Nút '{button_id}' không hợp lệ. Danh sách chấp nhận: btn_1 -> btn_12"
        }

    return {
        "success": True,
        "button_id": button_id,
        "name": slot_info["name"],
        "desc": slot_info["desc"],
        "message": f"Khởi chạy nút '{button_id}' thành công! (Sẵn sàng gán tính năng chi tiết)"
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
