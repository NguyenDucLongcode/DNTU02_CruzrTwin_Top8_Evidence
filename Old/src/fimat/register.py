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

# Import hàm cập nhật room devices
from src.fiware import update_room_devices

# ======================================================
# CONFIGURATION
# ======================================================

IOT_AGENT_URL = os.getenv(
    "IOT_AGENT_URL",
    os.getenv("FIMAT_API_URL", "http://localhost:4041")
)

APIKEY = os.getenv(
    "IOT_DEVICE_APIKEY",
    "cruzrtwin2026"
)

IOT_AGENT_RESOURCE = os.getenv(
    "IOT_AGENT_RESOURCE",
    "/iot/json"
)

# ======================================================
# FIWARE MULTI-TENANT CONFIG
# ======================================================

FIWARE_SERVICE = "cruzrtwin"
FIWARE_SERVICE_PATH = "/asean/buildings"

FIWARE_HEADERS = {
    "Content-Type": "application/json",
    "Fiware-Service": FIWARE_SERVICE,
    "Fiware-ServicePath": FIWARE_SERVICE_PATH,
}

# ======================================================
# REGISTER SERVICE GROUP
# ======================================================

def register_service_group() -> bool:
    """Tạo Service Group trong IoT Agent."""

    url = f"{IOT_AGENT_URL}/iot/services"

    payload = {
        "services": [
            {
                "apikey": APIKEY,
                "resource": IOT_AGENT_RESOURCE,
                "entity_type": "Device",
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

        if response.status_code in (200, 201, 204, 409):
            print(f"   Service group ready for resource {IOT_AGENT_RESOURCE}")
            return True

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
    """Đăng ký 1 thiết bị vào IoT Agent."""

    url = f"{IOT_AGENT_URL}/iot/devices"
    device_id = device_config["device_id"]

    # Xóa device cũ nếu có
    requests.delete(
        f"{url}/{device_id}",
        headers=FIWARE_HEADERS,
        timeout=10,
    )

    payload = {
        "devices": [
            {
                "device_id": device_id,
                "entity_name": device_config["entity_name"],
                "entity_type": device_config["entity_type"],
                "protocol": "PDI-IoTA-MQTT",
                "transport": "MQTT",
                "apikey": APIKEY,
                "resource": IOT_AGENT_RESOURCE,
                "attributes": device_config["attributes"],
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

        if response.status_code in (200, 201, 204):
            print(f"   Registered: {device_id}")
            return True
        elif response.status_code == 409:
            print(f"   Already Exists: {device_id}")
            return True
        else:
            print(f"      Failed: {device_id}")
            print(f"      Status: {response.status_code}")
            print(f"      Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"   Error: {e}")
        return False

# ======================================================
# GET DEVICE IDS FROM CONFIG
# ======================================================

def get_device_ids_from_config():
    """
    Lấy danh sách device IDs từ DEVICES_TO_REGISTER
    
    Returns:
        list: Danh sách entity_name của các thiết bị
    """
    device_ids = []
    for device in DEVICES_TO_REGISTER:
        # Lấy entity_name (đây là ID trong Orion)
        entity_name = device.get("entity_name")
        if entity_name:
            device_ids.append(entity_name)
    return device_ids

# ======================================================
# REGISTER ALL DEVICES
# ======================================================

def register_all_devices():
    """Đăng ký toàn bộ thiết bị và cập nhật vào Room."""

    print("\n" + "=" * 60)
    print("  FIWARE IoT Device Registration")
    print("=" * 60)

    print(f"   IoT Agent : {IOT_AGENT_URL}")
    print(f"   API Key   : {APIKEY}")
    print(f"   Service   : {FIWARE_SERVICE}")
    print(f"   Path      : {FIWARE_SERVICE_PATH}")
    print(f"   Resource  : {IOT_AGENT_RESOURCE}")

    print("-" * 60)

    # Tạo Service Group
    if not register_service_group():
        print("   Aborting device registration because service group setup failed.")
        return False

    # Hiển thị danh sách device
    print("    Devices to register:")

    for device in DEVICES_TO_REGISTER:
        print(
            f"      - {device['device_id']:<20} "
            f"{device['entity_name']:<20} "
            f"({device['entity_type']})"
        )

    print("-" * 60)

    # Đăng ký từng device
    success_count = 0

    for device in DEVICES_TO_REGISTER:
        if register_device(device):
            success_count += 1

    print("-" * 60)

    print(
        f" Result: "
        f"{success_count}/{len(DEVICES_TO_REGISTER)} "
        f"devices registered"
    )

    # ==================================================
    # CẬP NHẬT DANH SÁCH DEVICE VÀO ROOM
    # ==================================================
    
    if success_count > 0:
        print("-" * 60)
        print("   Updating Room with device list...")
        
        # Lấy danh sách device IDs từ config
        device_ids = get_device_ids_from_config()
        
        if device_ids:
            print(f"   Device IDs to update: {device_ids}")
            
            # Cập nhật vào Room entity
            if update_room_devices(device_ids):
                print(f"   ✅ Updated Room with {len(device_ids)} devices")
            else:
                print(f"   ⚠️ Failed to update Room devices")
        else:
            print("   ⚠️ No device IDs found to update")
    
    print("=" * 60)

    return success_count == len(DEVICES_TO_REGISTER)

# ======================================================
# MAIN
# ======================================================

if __name__ == "__main__":
    register_all_devices()