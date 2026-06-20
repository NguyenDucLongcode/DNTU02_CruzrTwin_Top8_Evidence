"""
========================================================
REPLAY HELPERS - CÁC HÀM TIỆN ÍCH CHO REPLAY TEST
========================================================

Tập hợp các hàm dùng chung cho replay test:
- Đọc file test
- Trích xuất giá trị cảm biến
- Tạo scenario_id động từ tên file
"""

import re
import logging
from pathlib import Path
from datetime import datetime, timezone
import json

logger = logging.getLogger("replay_helpers")


def load_test_files(test_dir: Path):
    """
    Lấy danh sách tất cả file JSON trong thư mục test
    
    Args:
        test_dir: Đường dẫn đến thư mục chứa file test
    
    Returns:
        List[Path]: Danh sách các file JSON đã được sắp xếp
    """
    files = sorted(test_dir.glob("*.json"))
    if not files:
        logger.warning(f"Không tìm thấy file JSON nào trong {test_dir}")
    return files

def load_test_file(file_path: Path) -> dict:
    """
    Đọc file test JSON và trả về nội dung
    
    Args:
        file_path: Đường dẫn đến file JSON
    
    Returns:
        dict: Nội dung file JSON, hoặc None nếu lỗi
    """
    logger = logging.getLogger("replay_helpers")
    
    # Kiểm tra file tồn tại
    if not file_path.exists():
        logger.warning(f"Không tìm thấy file: {file_path}")
        return None
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Lỗi đọc JSON từ {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Lỗi không xác định khi đọc file {file_path}: {e}")
        return None



def now_iso():
    """
    Tạo timestamp ISO 8601 hiện tại
    
    Returns:
        str: Timestamp dạng ISO 8601
    """
    return datetime.now(timezone.utc).isoformat()


def extract_all_readings(payload: dict) -> list:
    """
    Lấy tất cả readings từ file test
    
    Args:
        payload: Dict chứa dữ liệu từ file JSON
    
    Returns:
        list: Danh sách các readings (mỗi reading là 1 dict)
    """
    readings = payload.get("readings") or []
    return readings


def extract_device_values_from_reading(reading: dict) -> dict:
    """
    Trích xuất giá trị cảm biến từ 1 reading
    
    Args:
        reading: 1 dict chứa dữ liệu tại 1 thời điểm
    
    Returns:
        dict: Giá trị của 5 cảm biến (khớp với Device:TEMP_A101 và Device:ENERGY_E101)
    """
    return {
        # Thiết bị nhiệt độ (Device:TEMP_A101)
        "temp_sensor_a101": reading.get("temperature") or reading.get("temp") or 0,
        "humid_sensor_a101": reading.get("humidity") or 0,
        "air_sensor_a101": reading.get("co2") or reading.get("air_quality_or_co2") or 0,
        "smoke_sensor_a101": reading.get("smoke_status") or reading.get("smoke") or 0,
        
        # Thiết bị đo điện năng tiêu thụ (Device:ENERGY_E101)
        "energy_sensor_e101": reading.get("energy_consumption") or reading.get("energy") or 0,
    }


def extract_sequence_number(filename: str) -> str:
    """
    Trích xuất số thứ tự từ tên file
    
    Args:
        filename: Tên file (ví dụ: "critical_001.json" hoặc "normal_010.json")
    
    Returns:
        str: Số thứ tự (ví dụ: "001", "010")
    """
    match = re.search(r'(\d+)', filename)
    return match.group(1) if match else "001"


def extract_scenario_type(filename: str) -> str:
    """
    Xác định loại scenario từ tên file
    
    Args:
        filename: Tên file (ví dụ: "critical_001.json")
    
    Returns:
        str: "CRITICAL", "WARNING", hoặc "NORMAL"
    """
    if "critical" in filename.lower():
        return "CRITICAL"
    elif "warning" in filename.lower():
        return "WARNING"
    else:
        return "NORMAL"


def build_scenario_id(filename: str) -> str:
    """
    Tạo scenario_id từ tên file theo dạng SCN_{TYPE}_{NUMBER}
    
    Args:
        filename: Tên file (ví dụ: "critical_001.json")
    
    Returns:
        str: Scenario ID (ví dụ: "SCN_CRITICAL_001")
    """
    scenario_type = extract_scenario_type(filename)
    sequence_number = extract_sequence_number(filename)
    return f"SCN_{scenario_type}_{sequence_number}"


def get_device_status_from_filename(filename: str) -> str:
    """
    Xác định trạng thái thiết bị từ tên file
    
    Args:
        filename: Tên file (ví dụ: "critical_001.json")
    
    Returns:
        str: "CRITICAL", "WARNING", hoặc "NORMAL"
    """
    if "critical" in filename.lower():
        return "CRITICAL"
    elif "warning" in filename.lower():
        return "WARNING"
    else:
        return "NORMAL"