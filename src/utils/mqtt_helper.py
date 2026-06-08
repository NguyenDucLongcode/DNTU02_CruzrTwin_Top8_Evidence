"""
========================================================
MQTT HELPER UTILITIES
========================================================

Các hàm tiện ích dùng chung cho MQTT:
- Kết nối MQTT broker
- Gửi dữ liệu cho 1 device
- Gửi dữ liệu cho nhiều device
- Tạo payload theo đúng format
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from src.fiware.entities.query import get_room_state, get_all_devices, get_entity_by_type

from src.utils.replay_helpers import (
    build_scenario_id,
    get_device_status_from_filename,
)

# ======================================================
# CẤU HÌNH MẶC ĐỊNH
# ======================================================

DEFAULT_MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
DEFAULT_MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
DEFAULT_APIKEY = os.getenv("IOT_DEVICE_APIKEY", "cruzrtwin2026")
DEFAULT_DEMO_RUN_ID = os.getenv("DEMO_RUN_ID", "DNTU02_TOP8_RUN_2026_001")
DEFAULT_ZONE_ID = os.getenv("ZONE_ID", "DNTU_ROOM_A101")


# Log file paths
ORION_SYNC_LOG = os.path.join("logs", "SensorReading.jsonl")

# ======================================================
# MAP DEVICE ID → OBJECT ID
# ======================================================

OBJECT_ID_MAP = {
    "temp_sensor_a101": "t",
    "humid_sensor_a101": "h",
    "air_sensor_a101": "co2",
    "smoke_sensor_a101": "smoke",
    "smart_plug_a101": "energy"
}


# ======================================================
# HÀM MQTT CLIENT
# ======================================================

def create_mqtt_client(
    broker: str = DEFAULT_MQTT_BROKER,
    port: int = DEFAULT_MQTT_PORT
) -> mqtt.Client:
    """
    Tạo và kết nối MQTT client
    
    Args:
        broker: MQTT broker address (default: localhost)
        port: MQTT port (default: 1883)
    
    Returns:
        mqtt.Client: Đã kết nối
    """
    client = mqtt.Client()
    client.connect(broker, port, 60)
    client.loop_start()
    print(f" Connected to MQTT broker at {broker}:{port}")
    return client


def disconnect_mqtt_client(client: mqtt.Client):
    """Ngắt kết nối MQTT client"""
    client.loop_stop()
    client.disconnect()
    print("MQTT disconnected")


# ======================================================
# HÀM TẠO PAYLOAD
# ======================================================

def build_mqtt_payload(
    device_id: str,
    value,
    timestamp: Optional[str] = None
) -> dict:
    """
    Tạo payload MQTT cho 1 device
    
    Args:
        device_id: ID của thiết bị (vd: temp_sensor_a101)
        value: Giá trị cảm biến
        timestamp: Thời gian (tự tạo nếu None)
    
    Returns:
        dict: Payload MQTT
    """
    if timestamp is None:
       timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    
    obj_id = OBJECT_ID_MAP.get(device_id, "value")
    
    return {
        obj_id: value,
        "ts": timestamp
    }


def _append_jsonl(log_file: str, entry: dict):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

# ======================================================
# HÀM GỬI DỮ LIỆU
# ======================================================

def publish_device_data(
    client: mqtt.Client,
    device_id: str,
    value,
    apikey: str = DEFAULT_APIKEY,
    verbose: bool = True
) -> bool:
    """
    Gửi dữ liệu MQTT cho 1 device
    
    Args:
        client: MQTT client đã kết nối
        device_id: ID thiết bị
        value: Giá trị cảm biến
        apikey: API key (default: cruzrtwin2026)
        verbose: In log hay không (default: True)
    
    Returns:
        bool: True nếu thành công
    """
    topic = f"/{apikey}/{device_id}/attrs"
    payload = build_mqtt_payload(device_id, value)
    payload_text = json.dumps(payload, ensure_ascii=False)
    
    if verbose:
        print(f"   {device_id} → {value}")
    
    result = client.publish(topic, payload_text, qos=1)
    return result.rc == mqtt.MQTT_ERR_SUCCESS


def publish_multiple_devices(
    client: mqtt.Client,
    device_values: Dict[str, any],
    apikey: str = DEFAULT_APIKEY,
    delay: float = 0.5,
    verbose: bool = True
) -> int:
    """
    Gửi dữ liệu cho nhiều device cùng lúc
    
    Args:
        client: MQTT client đã kết nối
        device_values: Dict {device_id: value}
        apikey: API key
        delay: Thời gian delay giữa các device (giây)
        verbose: In log hay không
    
    Returns:
        int: Số device gửi thành công
    """
    success_count = 0
    total = len(device_values)
    
    for i, (device_id, value) in enumerate(device_values.items(), 1):
        if publish_device_data(client, device_id, value, apikey, verbose):
            success_count += 1
        if i < total:  # Không delay sau device cuối
            time.sleep(delay)
    
    return success_count

#======================================================
# HÀM TIỆN ÍCH CHO SHOW DEMO TRACE
def publish_scenario(
    device_values: Dict[str, any],
    scenario_name: str,
    apikey: str = DEFAULT_APIKEY,
    broker: str = DEFAULT_MQTT_BROKER,
    scenario_id: str = None,
    port: int = DEFAULT_MQTT_PORT,
    delay: float = 0.5
) -> bool:

   # Tạo MQTT client, gửi dữ liệu, rồi ngắt kết nối
    client = create_mqtt_client(
        broker,
        port
    )
 
  # Gửi dữ liệu qua MQTT sử dụng hàm tiện ích, đồng thời lưu log cho trace
    try:
        return publish_scenario_with_client(
            client=client,
            device_values=device_values,
            scenario_name=scenario_name,
            apikey=apikey,
            scenario_id=scenario_id,
            delay=delay,
        )
    finally:
        disconnect_mqtt_client(client)


# Hàm tiện ích chính để chạy 1 scenario với MQTT và lưu log trace
def publish_scenario_with_client(
    client,
    device_values: Dict[str, any],
    scenario_name: str,
    apikey: str = DEFAULT_APIKEY,
    scenario_id: str = None,
    delay: float = 0.05,
) -> bool:

    success_count = publish_multiple_devices(
        client,
        device_values,
        apikey,
        delay,
        verbose=True,
    )
 
     # Nếu tất cả device đều gửi thành công, thì lưu log trace scenario này vào orion_sync.jsonl
    if success_count == len(device_values):
        save_scenario_logs(
            device_values=device_values,
            scenario_name=scenario_name,
            scenario_id=scenario_id,
            demo_run_id=DEFAULT_DEMO_RUN_ID,
            zone_id=DEFAULT_ZONE_ID,
     )

    return success_count == len(device_values)


def save_scenario_logs(
    device_values,
    scenario_name,
    scenario_id,
    demo_run_id: str, 
    zone_id: str
):
    
    # Tạo scenario_id động nếu chưa có, và trích xuất device_status từ scenario_name
    scenario_id = build_scenario_id(scenario_id)
    scenario_name = f"REPLAY {scenario_name}"
    device_status = get_device_status_from_filename(scenario_name)

    # Lưu log vào orion_sync.jsonl để phục vụ cho trace và replay sau này
    sensor_entry =  {
        "demo_run_id": demo_run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "scenario_id": scenario_id,
        "zone_id": zone_id,
        "temperature": device_values.get("temp_sensor_a101", 0),
        "humidity": device_values.get("humid_sensor_a101", 0),
        "air_quality_or_co2": device_values.get("air_sensor_a101", 0),
        "smoke_status": device_values.get("smoke_sensor_a101", 0),
        "energy_consumption": device_values.get("smart_plug_a101", 0),
        "device_status": device_status,
    }
 

    _append_jsonl(ORION_SYNC_LOG, sensor_entry)

    print(f"   SensorReading log saved: {ORION_SYNC_LOG}")


# ======================================================
# TEST
# ======================================================

if __name__ == "__main__":
    # Test thử
    print("Testing MQTT Helper...")
    print(f"   OBJECT_ID_MAP: {OBJECT_ID_MAP}")
    print(" MQTT Helper ready!")