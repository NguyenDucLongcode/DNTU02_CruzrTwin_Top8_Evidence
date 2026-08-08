import sys
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from .client import TuyaCloudClient
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
from .commands import SmartPlugController, AudibleAlarmController, DoorLockController

def control_device(device_id: str, action: str, **kwargs) -> dict:
    """
    Điều khiển 1 thiết bị Tuya
    """

    client = TuyaCloudClient(device_id)
    
    # Xác định loại thiết bị dựa trên action
    if action == "on":
        # Thử các command phổ biến
        # Smart Plug: switch_1
        # Alarm: AlarmSwitch
        # Lock: manual_lock (không nên dùng lock/unlock từ xa)
        
        # Kiểm tra nếu có alarm_type thì đây là loa
        if "alarm_type" in kwargs or "duration" in kwargs:
            alarm_type = kwargs.get("alarm_type", 10)
            duration = kwargs.get("duration", 10)
            client.send_command("AlarmType", alarm_type)
            client.send_command("AlarmPeriod", duration)
            return client.send_command("AlarmSwitch", True)
        
        # Mặc định thử switch_1 (smart plug)
        return client.send_command("switch_1", True)
    
    elif action == "off":
        # Thử AlarmSwitch trước (cho loa)
        result = client.send_command("AlarmSwitch", False)
        if result.get("success") or result.get("result"):
            return result
        # Nếu không được, thử switch_1 (cho smart plug)
        return client.send_command("switch_1", False)
    
    elif action == "toggle":
        # Lấy trạng thái hiện tại
        status = client.get_status()
        
        # Kiểm tra từng attribute có thể
        current = status.get("switch_1", status.get("AlarmSwitch", status.get("manual_lock")))
        
        if current is not None:
            if current:
                return client.send_command("switch_1", False) if "switch_1" in status else client.send_command("AlarmSwitch", False)
            else:
                return client.send_command("switch_1", True) if "switch_1" in status else client.send_command("AlarmSwitch", True)
        
        return {"error": "Không thể xác định trạng thái hiện tại"}
    
    elif action == "status":
        return client.get_status()
    
    elif action == "lock":
        return client.send_command("manual_lock", True)
    
    elif action == "unlock":
        return client.send_command("manual_lock", False)
    
    else:
        return {"error": f"Hành động không hợp lệ: {action}"}

# ============================================================
# HÀM ĐIỀU KHIỂN SONG SONG NHIỀU THIẾT BỊ
# ============================================================

def control_multiple_devices(
    device_ids: List[str],
    action: str,
    device_type: str = "smart_plug",
    max_workers: int = 6,
    timeout: float = 30.0,
    async_exec: bool = False,
    **kwargs
) -> Dict[str, Dict]:
    """
    Điều khiển nhiều thiết bị cùng lúc (song song)
    """  
  
    
    def _control_one(device_id: str) -> tuple:
        """Điều khiển một thiết bị"""
        try:
            # Tạo controller phù hợp
            if device_type == "smart_plug":
                controller = SmartPlugController(device_id)
            elif device_type == "alarm":
                controller = AudibleAlarmController(device_id)
            elif device_type == "lock":
                controller = DoorLockController(device_id)
            else:
                raise ValueError(f"Không hỗ trợ loại thiết bị: {device_type}")
            
            # Thực hiện hành động
            action_str = f"[{device_type.upper()}] Gửi lệnh Tuya -> {action.upper()} ({device_id})"
            print(f"   🔌 {action_str}")
            if action == "on":
                if device_type == "alarm":
                    alarm_type = kwargs.get("alarm_type", 10)
                    duration = kwargs.get("duration", 10)
                    result = controller.turn_on(alarm_type, duration)
                else:
                    result = controller.turn_on()
            
            elif action == "off":
                result = controller.turn_off()
            
            elif action == "toggle":
                result = controller.toggle()
            
            elif action == "status":
                result = controller.get_all_status()
            
            elif action == "lock":
                if hasattr(controller, 'lock'):
                    result = controller.lock()
                else:
                    raise ValueError(f"Thiết bị {device_type} không hỗ trợ lock")
            
            elif action == "unlock":
                if hasattr(controller, 'unlock'):
                    result = controller.unlock()
                else:
                    raise ValueError(f"Thiết bị {device_type} không hỗ trợ unlock")
            
            # Phân tích chính xác phản hồi từ Tuya Cloud API
            device_executed = False
            error_reason = ""

            if isinstance(result, dict):
                if result.get("result") is True:
                    device_executed = True
                elif result.get("result") is False:
                    device_executed = False
                    error_reason = "Thiết bị Tuya thật không kết nối (OFFLINE / Unreachable)"
                elif result.get("success") is True and "result" not in result:
                    device_executed = True
                else:
                    error_reason = result.get("msg") or result.get("error") or f"Lỗi phản hồi: {result}"
            else:
                error_reason = f"Phản hồi không hợp lệ: {result}"

            if device_executed:
                print(f"   ✅ TUYA THÀNH CÔNG ({device_id}): Thiết bị đã nhận lệnh [{action.upper()}] thành công!")
                return (device_id, {"success": True, "executed": True, "result": result})
            else:
                print(f"   ❌ TUYA THẤT BẠI ({device_id}): {error_reason}")
                return (device_id, {"success": False, "executed": False, "error": error_reason, "raw_result": result})
        
        except Exception as e:
            print(f"   ❌ LỖI KẾT NỐI TUYA ({device_id}): {e}")
            return (device_id, {"success": False, "executed": False, "error": str(e)})
    
    # Hàm phát lệnh song song
    def _execute_parallel():
        import time
        t_overall_start = time.perf_counter()
        results = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_control_one, device_id): device_id
                for device_id in device_ids
            }

            for future in as_completed(futures, timeout=timeout):
                device_id, result = future.result()
                results[device_id] = result

        t_overall_end = time.perf_counter()
        overall_elapsed_ms = (t_overall_end - t_overall_start) * 1000
        print(f"⏱️ [OVERALL TUYA TIMING] Điều khiển song song {len(device_ids)} thiết bị hoàn tất trong: {overall_elapsed_ms:.2f} ms ({overall_elapsed_ms/1000:.2f}s)")
        return results

    if async_exec:
        import threading
        print(f"⚡ [NON-BLOCKING ASYNC] Phát lệnh Tuya [{action.upper()}] tức thì cho {len(device_ids)} thiết bị trong background thread...")
        threading.Thread(target=_execute_parallel, daemon=True).start()
        return {
            device_id: {
                "success": True,
                "executed": True,
                "async": True,
                "message": f"⚡ Lệnh Tuya {action.upper()} đã được phát đi tức thì (Non-blocking)!"
            }
            for device_id in device_ids
        }
    else:
        return _execute_parallel()

# ============================================================
# HÀM TIỆN ÍCH CHO FIWARE ID (tự động mapping)
# ============================================================

def control_device_by_fiware_id(fiware_id: str, action: str, **kwargs) -> dict:
    """
    Điều khiển 1 thiết bị bằng FIWARE device_id (tự động mapping)
    
    Args:
        fiware_id: FIWARE device_id (vd: "smart_plug_a106")
        action: Hành động cần thực hiện
        **kwargs: Tham số bổ sung
    
    Returns:
        dict: Kết quả trả về
    
    Ví dụ:
        result = control_device_by_fiware_id("smart_plug_a106", "on")
        result = control_device_by_fiware_id("audible_alarm_a101", "on", alarm_type=10)
    """
    from .fiware_adapter import get_adapter
    
    adapter = get_adapter()
    tuya_id = adapter.get_tuya_id(fiware_id)
    
    if not tuya_id:
        return {"error": f"Không tìm thấy mapping cho: {fiware_id}"}
    
    return control_device(tuya_id, action, **kwargs)

def control_multiple_by_fiware_ids(
    fiware_ids: List[str],
    action: str,
    device_type: str = "smart_plug",
    max_workers: int = 6,
    timeout: float = 30.0,
    async_exec: bool = False,
    **kwargs
) -> Dict[str, Dict]:
    """
    Điều khiển nhiều thiết bị từ FIWARE device_id (tự động mapping)

    Args:
        fiware_ids: Danh sách FIWARE device_id
        action: Hành động cần thực hiện
        device_type: Loại thiết bị
        max_workers: Số luồng tối đa
        timeout: Thời gian chờ tối đa
        async_exec: Thực thi bất đồng bộ không làm block caller (mặc định True)

    Returns:
        Dict: Kết quả từng thiết bị với FIWARE ID
    """
    from .fiware_adapter import get_adapter

    adapter = get_adapter()
    results = {}

    # Chuyển đổi FIWARE ID -> Tuya ID
    tuya_ids = []
    for fiware_id in fiware_ids:
        tuya_id = adapter.get_tuya_id(fiware_id)
        if tuya_id:
            tuya_ids.append((fiware_id, tuya_id))
        else:
            results[fiware_id] = {"success": False, "error": f"Không tìm thấy mapping cho {fiware_id}"}

    # Điều khiển các thiết bị đã mapping được
    if tuya_ids:
        # Lấy danh sách Tuya IDs
        tuya_only_ids = [tid for _, tid in tuya_ids]

        # Gọi hàm điều khiển song song bất đồng bộ
        tuya_results = control_multiple_devices(
            device_ids=tuya_only_ids,
            action=action,
            device_type=device_type,
            max_workers=max_workers,
            timeout=timeout,
            async_exec=async_exec,
            **kwargs
        )
        
        # Chuyển đổi kết quả về FIWARE ID
        results = {}
        for fiware_id, tuya_id in tuya_ids:
            if tuya_id in tuya_results:
                results[fiware_id] = tuya_results[tuya_id]
            else:
                results[fiware_id] = {"success": False, "error": "Không có kết quả"}
    
    return results


# ============================================================
# CÁC HÀM TIỆN ÍCH CHO SMART PLUG
# ============================================================

def turn_on_all_plugs(device_ids: List[str], max_workers: int = 6) -> Dict[str, Dict]:
    """Bật tất cả ổ cắm trong danh sách (song song)"""
    return control_multiple_devices(device_ids, "on", "smart_plug", max_workers)


def turn_off_all_plugs(device_ids: List[str], max_workers: int = 6) -> Dict[str, Dict]:
    """Tắt tất cả ổ cắm trong danh sách (song song)"""
    return control_multiple_devices(device_ids, "off", "smart_plug", max_workers)


def toggle_all_plugs(device_ids: List[str], max_workers: int = 6) -> Dict[str, Dict]:
    """Đảo trạng thái tất cả ổ cắm trong danh sách (song song)"""
    return control_multiple_devices(device_ids, "toggle", "smart_plug", max_workers)


def get_all_plugs_status(device_ids: List[str], max_workers: int = 6) -> Dict[str, Dict]:
    """Lấy trạng thái tất cả ổ cắm trong danh sách (song song)"""
    return control_multiple_devices(device_ids, "status", "smart_plug", max_workers)