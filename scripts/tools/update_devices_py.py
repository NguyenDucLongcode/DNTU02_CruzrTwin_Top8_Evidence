import re

file_path = "src/iot/devices.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Tạo code thay thế
new_devices_code = """DEVICES_TO_REGISTER = []
_ROOMS = ["A101", "A102", "A103", "A104", "A105", "A106"]

for _room in _ROOMS:
    DEVICES_TO_REGISTER.extend([
        {
            "device_id": f"temp_sensor_{_room.lower()}",
            "entity_name": f"Device:TEMP_{_room}",
            "entity_type": "TemperatureSensor",
            "protocol": "PDI-IoTA-UltraLight",
            "transport": "MQTT",
            "timezone": "Asia/Ho_Chi_Minh",
            "attributes": [
                {"object_id": "t", "name": "temperature", "type": "Number"}
            ],
            "static_attributes": [
                {"name": "demo_run_id", "type": "Text", "value": DEMO_RUN_ID},
                {"name": "zone_id", "type": "Text", "value": f"DNTU_ROOM_{_room}"},
                {"name": "room_id", "type": "Text", "value": _room}
            ]
        },
        {
            "device_id": f"smoke_sensor_{_room.lower()}",
            "entity_name": f"Device:SMOKE_{_room}",
            "entity_type": "SmokeDetector",
            "protocol": "PDI-IoTA-UltraLight",
            "transport": "MQTT",
            "timezone": "Asia/Ho_Chi_Minh",
            "attributes": [
                {"object_id": "smoke", "name": "smoke_status", "type": "Number"}
            ],
            "static_attributes": [
                {"name": "demo_run_id", "type": "Text", "value": DEMO_RUN_ID},
                {"name": "zone_id", "type": "Text", "value": f"DNTU_ROOM_{_room}"},
                {"name": "room_id", "type": "Text", "value": _room}
            ]
        },
        {
            "device_id": f"air_sensor_{_room.lower()}",
            "entity_name": f"Device:AIR_{_room}",
            "entity_type": "AirQualitySensor",
            "protocol": "PDI-IoTA-UltraLight",
            "transport": "MQTT",
            "timezone": "Asia/Ho_Chi_Minh",
            "attributes": [
                {"object_id": "co2", "name": "co2", "type": "Number"}
            ],
            "static_attributes": [
                {"name": "demo_run_id", "type": "Text", "value": DEMO_RUN_ID},
                {"name": "zone_id", "type": "Text", "value": f"DNTU_ROOM_{_room}"},
                {"name": "room_id", "type": "Text", "value": _room}
            ]
        },
        {
            "device_id": f"presence_sensor_{_room.lower()}",
            "entity_name": f"Device:PRESENCE_{_room}",
            "entity_type": "PresenceSensor",
            "protocol": "PDI-IoTA-UltraLight",
            "transport": "MQTT",
            "timezone": "Asia/Ho_Chi_Minh",
            "attributes": [
                {"object_id": "presence", "name": "presence", "type": "Number"}
            ],
            "static_attributes": [
                {"name": "demo_run_id", "type": "Text", "value": DEMO_RUN_ID},
                {"name": "zone_id", "type": "Text", "value": f"DNTU_ROOM_{_room}"},
                {"name": "room_id", "type": "Text", "value": _room}
            ]
        }
    ])
"""

# Extract everything before DEVICES_TO_REGISTER and everything after the list
start_idx = content.find("DEVICES_TO_REGISTER = [")
if start_idx != -1:
    # Find the matching closing bracket for DEVICES_TO_REGISTER
    bracket_count = 0
    in_string = False
    escape = False
    string_char = None
    end_idx = -1
    
    for i in range(start_idx, len(content)):
        char = content[i]
        
        if escape:
            escape = False
            continue
            
        if char == '\\':
            escape = True
            continue
            
        if in_string:
            if char == string_char:
                in_string = False
            continue
            
        if char in ("'", '"'):
            in_string = True
            string_char = char
            continue
            
        if char == '[':
            bracket_count += 1
        elif char == ']':
            bracket_count -= 1
            if bracket_count == 0:
                end_idx = i + 1
                break
                
    if end_idx != -1:
        new_content = content[:start_idx] + new_devices_code + content[end_idx:]
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Updated devices.py successfully!")
    else:
        print("Could not find closing bracket.")
else:
    print("Could not find DEVICES_TO_REGISTER.")
