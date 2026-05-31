"""
Truy vấn dữ liệu từ Orion
"""

from ..client import get_entities, get_entity


def get_room_state(zone_id: str = None) -> dict:
    """Lấy trạng thái của Room"""
    entity_id = f"Room:{zone_id}" if zone_id else "Room:DNTU_ROOM_A101"
    return get_entity(entity_id)


def get_all_devices() -> list:
    """Lấy tất cả Device entities"""
    entities = get_entities()
    return [e for e in entities if e.get("type", "").endswith("Sensor")]


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