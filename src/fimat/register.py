"""
========================================================
FIWARE IoT Agent Device Registration
MQTT → IoT Agent → Orion Context Broker
========================================================

Mục đích:
- Tạo Service Group trong IoT Agent
- Đăng ký toàn bộ IoT devices
- Cho phép thiết bị gửi dữ liệu MQTT → Orion

Luồng hoạt động:

Device MQTT
    ↓
IoT Agent
    ↓
Orion Context Broker
"""

import os
import sys
import requests

# ======================================================
# IMPORT PATH
# ======================================================

# Lấy thư mục gốc của project
# để có thể import các module nội bộ
ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

# Thêm ROOT_DIR vào Python path
sys.path.insert(0, ROOT_DIR)

# ======================================================
# IMPORT DEVICE CONFIG
# ======================================================

# Danh sách tất cả thiết bị cần đăng ký
from src.iot.devices import DEVICES_TO_REGISTER

# ======================================================
# CONFIGURATION
# ======================================================

# URL của FIWARE IoT Agent
#
# Ưu tiên:
# 1. IOT_AGENT_URL
# 2. FIMAT_API_URL
# 3. fallback localhost
#
# Ví dụ:
# http://localhost:4041
IOT_AGENT_URL = os.getenv(
    "IOT_AGENT_URL",
    os.getenv("FIMAT_API_URL", "http://localhost:4041")
)

# API Key dùng chung cho tất cả thiết bị
#
# MQTT device bắt buộc phải gửi đúng APIKEY
# thì IoT Agent mới chấp nhận dữ liệu
#
# Ví dụ MQTT topic:
# /iot/json/cruzrtwin2026/device001/attrs
APIKEY = os.getenv(
    "IOT_DEVICE_APIKEY",
    "cruzrtwin2026"
)

# Resource dùng chung cho tất cả thiết bị
#
# Resource sẽ xuất hiện trong MQTT endpoint
#
# Ví dụ:
# /iot/json
IOT_AGENT_RESOURCE = os.getenv(
    "IOT_AGENT_RESOURCE",
    "/iot/json"
)

# ======================================================
# FIWARE MULTI-TENANT CONFIG
# ======================================================

# Namespace/service chính
#
# Tương tự tenant hoặc project
FIWARE_SERVICE = "cruzrtwin"

# Nhóm logical path của dữ liệu
#
# Tương tự folder hoặc domain dữ liệu
FIWARE_SERVICE_PATH = "/asean/buildings"

# ======================================================
# FIWARE HEADERS
# ======================================================

# Header bắt buộc khi làm việc với FIWARE
#
# Fiware-Service:
#     xác định tenant/service
#
# Fiware-ServicePath:
#     xác định logical path
FIWARE_HEADERS = {
    "Content-Type": "application/json",
    "Fiware-Service": FIWARE_SERVICE,
    "Fiware-ServicePath": FIWARE_SERVICE_PATH,
}

# ======================================================
# REGISTER SERVICE GROUP
# ======================================================

def register_service_group() -> bool:
    """
    Tạo Service Group trong IoT Agent.

    Service Group giúp IoT Agent biết:
    - API Key nào hợp lệ
    - Resource nào được phép dùng
    - Dữ liệu sẽ forward sang Orion nào

    Nếu service group đã tồn tại:
    → IoT Agent trả về 409
    → vẫn xem là thành công
    """

    url = f"{IOT_AGENT_URL}/iot/services"

    payload = {
        "services": [
            {
                # API Key xác thực device
                "apikey": APIKEY,

                # MQTT resource
                "resource": IOT_AGENT_RESOURCE,

                # Entity type mặc định
                "entity_type": "Device",

                # Địa chỉ Orion Context Broker
                "cbroker": "http://orion:1026",
            }
        ]
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=FIWARE_HEADERS,
            timeout=10,
        )

        # Thành công hoặc đã tồn tại
        if response.status_code in (200, 201, 204, 409):
            print(f"   Service group ready for resource {IOT_AGENT_RESOURCE}")
            return True

        # Lỗi đăng ký
        print(f"   Failed service group registration: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        return False

    except Exception as e:
        print(f"   Error registering service group: {e}")
        return False

# ======================================================
# REGISTER DEVICE
# ======================================================

def register_device(device_config: dict):
    """
    Đăng ký 1 thiết bị vào IoT Agent.

    Sau khi đăng ký:
    - IoT Agent sẽ nhận dữ liệu MQTT
    - map dữ liệu thành entity NGSI
    - gửi sang Orion
    """

    url = f"{IOT_AGENT_URL}/iot/devices"

    # ID thiết bị MQTT
    device_id = device_config["device_id"]

    # --------------------------------------------------
    # XÓA DEVICE CŨ (nếu có)
    # --------------------------------------------------
    #
    # Mục đích:
    # - tránh conflict
    # - cập nhật config mới nhất
    # - đảm bảo apikey/resource đúng
    #
    requests.delete(
        f"{url}/{device_id}",
        headers=FIWARE_HEADERS,
        timeout=10,
    )

    # --------------------------------------------------
    # PAYLOAD ĐĂNG KÝ DEVICE
    # --------------------------------------------------

    payload = {
        "devices": [
            {
                # ID device MQTT
                "device_id": device_id,

                # Tên entity trong Orion
                "entity_name": device_config["entity_name"],

                # Loại entity
                "entity_type": device_config["entity_type"],

                # Protocol của IoT Agent
                "protocol": "PDI-IoTA-MQTT",

                # Transport layer
                "transport": "MQTT",

                # API Key xác thực
                "apikey": APIKEY,

                # MQTT resource
                "resource": IOT_AGENT_RESOURCE,

                # Dynamic attributes
                #
                # Ví dụ:
                # temperature
                # humidity
                "attributes": device_config["attributes"],

                # Static attributes
                #
                # Ví dụ:
                # room
                # floor
                # building
                "static_attributes": device_config["static_attributes"]
            }
        ]
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=FIWARE_HEADERS,
            timeout=10
        )

        # Đăng ký thành công
        if response.status_code in (200, 201, 204):
            print(f"   Registered: {device_id}")
            return True

        # Device đã tồn tại
        elif response.status_code == 409:
            print(f"   Already Exists: {device_id}")
            return True

        # Đăng ký thất bại
        else:
            print(f"      Failed: {device_id}")
            print(f"      Status: {response.status_code}")
            print(f"      Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"   Error: {e}")
        return False

# ======================================================
# REGISTER ALL DEVICES
# ======================================================

def register_all_devices():
    """
    Đăng ký toàn bộ thiết bị.
    """

    print("\n" + "=" * 60)
    print("  FIWARE IoT Device Registration")
    print("=" * 60)

    print(f"   IoT Agent : {IOT_AGENT_URL}")
    print(f"   API Key   : {APIKEY}")
    print(f"   Service   : {FIWARE_SERVICE}")
    print(f"   Path      : {FIWARE_SERVICE_PATH}")
    print(f"   Resource  : {IOT_AGENT_RESOURCE}")

    print("-" * 60)

    # --------------------------------------------------
    # TẠO SERVICE GROUP
    # --------------------------------------------------

    if not register_service_group():
        print("   Aborting device registration because service group setup failed.")
        return False

    # --------------------------------------------------
    # HIỂN THỊ DANH SÁCH DEVICE
    # --------------------------------------------------

    print("    Devices to register:")

    for device in DEVICES_TO_REGISTER:
        print(
            f"      • "
            f"{device['device_id']} "
            f"→ "
            f"{device['entity_name']} "
            f"({device['entity_type']})"
        )

    print("-" * 60)

    # --------------------------------------------------
    # ĐĂNG KÝ TỪNG DEVICE
    # --------------------------------------------------

    success_count = 0

    for device in DEVICES_TO_REGISTER:
        if register_device(device):
            success_count += 1

    # --------------------------------------------------
    # KẾT QUẢ
    # --------------------------------------------------

    print("-" * 60)

    print(
        f" Result: "
        f"{success_count}/{len(DEVICES_TO_REGISTER)} "
        f"devices registered"
    )

    print("=" * 60)

    return success_count == len(DEVICES_TO_REGISTER)

# ======================================================
# MAIN
# ======================================================

if __name__ == "__main__":

    # Chạy đăng ký toàn bộ thiết bị
    register_all_devices()