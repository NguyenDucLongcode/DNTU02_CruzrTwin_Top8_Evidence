"""
Truy vấn dữ liệu từ Orion
"""

from ..client import get_entities, get_entity


def get_room_state(zone_id: str = None) -> dict:
    """Lấy trạng thái của Room"""
    entity_id = f"Room:{zone_id}" if zone_id else "Room:DNTU_ROOM_A101"
    return get_entity(entity_id)


def get_all_devices() -> list:
    """Lấy tất cả Device entities (bao gồm Sensor, Detector, Plug, ...)"""
    entities = get_entities()
    # Lấy tất cả entity có id bắt đầu bằng "Device:"
    return [e for e in entities if e.get("id", "").startswith("Device:")]


def get_entity_by_type(entity_type: str) -> list:
    """Lấy entities theo type"""
    entities = get_entities(params={"type": entity_type})
    return entities


def get_entity_by_type(entity_type: str) -> list:
    """Lấy entities theo type"""
    entities = get_entities(params={"type": entity_type})
    return entities


def print_summary():
    """In tóm tắt đẹp mắt (dùng cho demo)"""
    entities = get_entities()
    
    print("\n" + "=" * 60)
    print(" FIWARE ORION - ENTITIES SUMMARY")
    print("=" * 60)
    
    if not entities:
        print("   No entities found")
    else:
        for entity in entities:
            entity_id = entity.get("id", "unknown")
            entity_type = entity.get("type", "unknown")
            print(f"\n   🔹 {entity_id} ({entity_type})")
            
            for key, val in entity.items():
                if key not in ["id", "type"] and isinstance(val, dict):
                    value = val.get("value", "N/A")
                    print(f"        {key}: {value}")
    
    print("=" * 60)

def get_alert_events() -> list:
    """Lấy tất cả AlertEvent entities (theo file Word 4.2)"""
    entities = get_entities(params={"type": "AlertEvent"})
    return entities


def get_robot_actions() -> list:
    """Lấy tất cả RobotAction entities (theo file Word 4.2)"""
    entities = get_entities(params={"type": "RobotAction"})
    return entities


def get_all_devices_in_room(zone_id: str = None) -> dict:
    """
    Lấy tất cả thiết bị trong room từ FIWARE
    """
    if zone_id is None:
        zone_id = ZONE_ID
    
    # Lấy Room entity
    room = get_room_state(zone_id) or {}
    
    # Lấy danh sách device_ids từ room (theo code cũ của bạn)
    devices = room.get("device_ids", [])
    

    
    return devices


def get_smart_plugs_in_room(zone_id: str = None) -> list:
    """
    Lấy danh sách smart_plug trong room
    
    Args:
        zone_id: ID của zone/phòng (mặc định: ZONE_ID từ env)
    
    Returns:
        list: Danh sách smart_plug IDs (dạng smart_plug_a101, ...)
    """
    if zone_id is None:
        zone_id = ZONE_ID
    
    # Lấy danh sách device_ids từ room
    device_ids = get_all_devices_in_room(zone_id)
    
    # Lấy danh sách thiết bị từ device_ids
    # Cấu trúc: device_ids có thể là dict với key 'value' hoặc list
    if isinstance(device_ids, dict) and "value" in device_ids:
        device_list = device_ids["value"]
    elif isinstance(device_ids, list):
        device_list = device_ids
    else:
        device_list = []
    
    # Lọc ra smart_plug
    smart_plugs = []
    for device in device_list:
        if not device:
            continue
        
        if isinstance(device, str):
            # Lấy tên device (phần sau dấu :)
            device_name = device.split(":")[-1] if ":" in device else device
            
            # Kiểm tra nếu là PLUG (chứa từ PLUG)
            if "PLUG" in device_name:
                # Chuyển Device:PLUG_A101 -> smart_plug_a101
                plug_id = device_name.lower().replace("plug_", "smart_plug_")
                smart_plugs.append(plug_id)
    
    return smart_plugs


def get_alarms_in_room(zone_id: str = None) -> list:
    """
    Lấy danh sách loa báo động (alarm) trong room
    
    Args:
        zone_id: ID của zone/phòng (mặc định: ZONE_ID từ env)
    
    Returns:
        list: Danh sách alarm IDs (dạng audible_alarm_a101, ...)
    """
    if zone_id is None:
        zone_id = ZONE_ID
    
    # Lấy danh sách device_ids từ room
    device_ids = get_all_devices_in_room(zone_id)
    
    # Lấy danh sách thiết bị từ device_ids
    if isinstance(device_ids, dict) and "value" in device_ids:
        device_list = device_ids["value"]
    elif isinstance(device_ids, list):
        device_list = device_ids
    else:
        device_list = []
    
    # Lọc ra alarm
    alarms = []
    for device in device_list:
        if not device:
            continue
        
        if isinstance(device, str):
            # Lấy tên device (phần sau dấu :)
            device_name = device.split(":")[-1] if ":" in device else device
            
            # Kiểm tra nếu là ALARM hoặc SIREN
            if "ALARM" in device_name or "SIREN" in device_name:
                # Chuyển Device:ALARM_A101 -> audible_alarm_a101
                alarm_id = device_name.lower().replace("alarm_", "audible_alarm_")
                alarms.append(alarm_id)
    
    return alarms


def get_locks_in_room(zone_id: str = None) -> list:
    """
    Lấy danh sách khóa cửa (lock) trong room
    
    Args:
        zone_id: ID của zone/phòng (mặc định: ZONE_ID từ env)
    
    Returns:
        list: Danh sách lock IDs (dạng lock_door_a101, ...)
    """
    if zone_id is None:
        zone_id = ZONE_ID
    
    # Lấy danh sách device_ids từ room
    device_ids = get_all_devices_in_room(zone_id)
    
    # Lấy danh sách thiết bị từ device_ids
    if isinstance(device_ids, dict) and "value" in device_ids:
        device_list = device_ids["value"]
    elif isinstance(device_ids, list):
        device_list = device_ids
    else:
        device_list = []
    
    # Lọc ra lock
    locks = []
    for device in device_list:
        if not device:
            continue
        
        if isinstance(device, str):
            # Lấy tên device (phần sau dấu :)
            device_name = device.split(":")[-1] if ":" in device else device
            
            # Kiểm tra nếu là LOCK
            if "LOCK" in device_name:
                # Chuyển Device:LOCK_A101 -> lock_door_a101
                lock_id = device_name.lower().replace("lock_", "lock_door_")
                locks.append(lock_id)
    
    return locks