"""
========================================================
REALISTIC IoT DIGITAL TWIN CONFIGURATION
FIWARE + Orion Context Broker + Smart Building Demo
========================================================

Smart Building Digital Twin:
- MQTT Sensors
- IoT Agent
- Orion Context Broker
- AI Alert System
- Cruzr Robot Integration
"""

# ======================================================
# GLOBAL CONFIGURATION
# ======================================================

DEMO_RUN_ID = "DNTU02_TOP8_RUN_2026_001"
ZONE_ID = "DNTU_ROOM_A101"
BUILDING_ID = "DNTU_BUILDING_A"


# ======================================================
# ROOM ENTITY CONFIG
# ======================================================

ROOM_CONFIG = {
    "id": f"Room:{ZONE_ID}",
    "type": "Room",

    "attributes": [

        # ==================================================
        # CORE IDENTIFIERS
        # ==================================================
        {"name": "demo_run_id", "type": "Text"},
        {"name": "zone_id", "type": "Text"},
        {"name": "scenario_id", "type": "Text"},

        # ==================================================
        # ENVIRONMENTAL DATA
        # ==================================================
        {"name": "temperature", "type": "Number"},
        {"name": "humidity", "type": "Number"},
        {"name": "co2", "type": "Number"},
        {"name": "smoke_status", "type": "Number"},
        {"name": "energy_consumption", "type": "Number"},

        # ==================================================
        # DEVICE INFO - CHỈ LƯU DANH SÁCH THIẾT BỊ
        # ==================================================
        {"name": "device_ids", "type": "Array"},  # ["Device:TEMP_A101", "Device:ENERGY_E101"]

        # ==================================================
        # ROOM STATUS
        # ==================================================
        {"name": "device_status", "type": "Text"},
        {"name": "air_quality_status", "type": "Text"},
        {"name": "safety_status", "type": "Text"},
        {"name": "risk_level", "type": "Text"},
        {"name": "occupancy_status", "type": "Text"},
        {"name": "anomaly_detected", "type": "Boolean"},

        # ==================================================
        # AI / ALERT DATA
        # ==================================================
        {"name": "risk_score", "type": "Number"},
        {"name": "ai_confidence", "type": "Number"},
        {"name": "anomaly_score", "type": "Number"},
        {"name": "predicted_event", "type": "Text"},
        {"name": "recommended_action", "type": "Text"},

        # ==================================================
        # ROOM THRESHOLDS
        # ==================================================
        {"name": "temperature_warning_threshold", "type": "Number"},
        {"name": "temperature_critical_threshold", "type": "Number"},

        {"name": "humidity_warning_threshold", "type": "Number"},
        {"name": "humidity_critical_threshold", "type": "Number"},

        {"name": "co2_warning_threshold", "type": "Number"},
        {"name": "co2_critical_threshold", "type": "Number"},

        # ==================================================
        # BUILDING METADATA
        # ==================================================
        {"name": "building_id", "type": "Text"},
        {"name": "floor", "type": "Number"},
        {"name": "room_name", "type": "Text"},
        {"name": "room_type", "type": "Text"},
        {"name": "capacity", "type": "Number"},

        # ==================================================
        # ROBOT / EMERGENCY STATUS
        # ==================================================
        {"name": "robot_response_required", "type": "Boolean"},
        {"name": "robot_status", "type": "Text"},
        {"name": "evacuation_status", "type": "Text"},
        {"name": "emergency_level", "type": "Text"},

        # ==================================================
        # TIMESTAMP
        # ==================================================
        {"name": "timestamp", "type": "DateTime"},
        {"name": "last_updated", "type": "DateTime"},
    ]
}

# ======================================================
# DEVICE DEFINITIONS
# ======================================================

DEVICES_TO_REGISTER = []
_ROOMS = ["L1-A1", "L1-A2", "L1-A3", "L1-A4", "L1-A5"]

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



# ======================================================
# ALERT EVENT TEMPLATE
# ======================================================

ALERT_EVENT_TEMPLATE = {
    "id": "AlertEvent:SCN_CRITICAL_001",
    "type": "AlertEvent",

    "attributes": [

        # ==================================================
        # CORE IDENTIFIERS
        # ==================================================
        {"name": "demo_run_id", "type": "Text"},
        {"name": "zone_id", "type": "Text"},
        {"name": "scenario_id", "type": "Text"},

        # ==================================================
        # ALERT INFORMATION
        # ==================================================
        {"name": "alert_type", "type": "Text"},
        {"name": "severity", "type": "Text"},
        {"name": "status", "type": "Text"},
        {"name": "message", "type": "Text"},

        # ==================================================
        # SOURCE INFORMATION
        # ==================================================
        {"name": "source_room", "type": "Text"},
        {"name": "source_device", "type": "Text"},
        {"name": "trigger_sensor", "type": "Text"},

        # ==================================================
        # SENSOR VALUES
        # ==================================================
        {"name": "temperature", "type": "Number"},
        {"name": "humidity", "type": "Number"},
        {"name": "co2", "type": "Number"},
        {"name": "smoke_status", "type": "Number"},
        {"name": "energy_consumption", "type": "Number"},

        # ==================================================
        # AI ANALYSIS
        # ==================================================
        {"name": "risk_score", "type": "Number"},
        {"name": "ai_confidence", "type": "Number"},
        {"name": "anomaly_score", "type": "Number"},
        {"name": "predicted_level", "type": "Text"},
        {"name": "recommended_action", "type": "Text"},
        {"name": "ai_model", "type": "Text"},

        # ==================================================
        # ROBOT RESPONSE
        # ==================================================
        {"name": "requires_robot_response", "type": "Boolean"},
        {"name": "robot_dispatched", "type": "Boolean"},
        {"name": "robot_id", "type": "Text"},

        # ==================================================
        # EMERGENCY WORKFLOW
        # ==================================================
        {"name": "acknowledged", "type": "Boolean"},
        {"name": "resolved", "type": "Boolean"},
        {"name": "emergency_level", "type": "Text"},

        # ==================================================
        # TIMESTAMP
        # ==================================================
        {"name": "timestamp", "type": "DateTime"},
        {"name": "resolved_at", "type": "DateTime"},
    ]
}


# ======================================================
# ROBOT ACTION TEMPLATE
# ======================================================

ROBOT_ACTION_TEMPLATE = {
    "id": "RobotAction:CRUZR_ACTION_001",
    "type": "RobotAction",

    "attributes": [

        # ==================================================
        # CORE IDENTIFIERS
        # ==================================================
        {"name": "demo_run_id", "type": "Text"},
        {"name": "zone_id", "type": "Text"},
        {"name": "scenario_id", "type": "Text"},

        # ==================================================
        # ROBOT INFO
        # ==================================================
        {"name": "robot_id", "type": "Text"},
        {"name": "robot_model", "type": "Text"},
        {"name": "battery_level", "type": "Number"},

        # ==================================================
        # ACTION INFO
        # ==================================================
        {"name": "action_type", "type": "Text"},
        {"name": "target_room", "type": "Text"},
        {"name": "priority", "type": "Text"},

        # ==================================================
        # COMMUNICATION
        # ==================================================
        {"name": "voice_message", "type": "Text"},
        {"name": "display_message", "type": "Text"},

        # ==================================================
        # NAVIGATION
        # ==================================================
        {"name": "navigation_status", "type": "Text"},
        {"name": "current_location", "type": "Text"},
        {"name": "destination_reached", "type": "Boolean"},

        # ==================================================
        # TASK EXECUTION
        # ==================================================
        {"name": "task_status", "type": "Text"},
        {"name": "action_result", "type": "Text"},
        {"name": "response_time_ms", "type": "Number"},

        # ==================================================
        # SYSTEM STATUS
        # ==================================================
        {"name": "status", "type": "Text"},
        {"name": "connectivity", "type": "Text"},

        # ==================================================
        # TIMESTAMP
        # ==================================================
        {"name": "timestamp", "type": "DateTime"},
        {"name": "completed_at", "type": "DateTime"},
    ]
}


# ======================================================
# STATUS ENUMS
# ======================================================

DEVICE_STATUSES = ["online", "offline", "warning", "critical"]

CONNECTIVITY_STATUSES = [
    "connected",
    "weak_signal",
    "disconnected"
]

AIR_QUALITY_STATUSES = [
    "good",
    "moderate",
    "unhealthy",
    "hazardous"
]

SAFETY_STATUSES = [
    "safe",
    "warning",
    "danger"
]

ALERT_SEVERITIES = [
    "low",
    "medium",
    "high",
    "critical"
]

ROBOT_STATUSES = [
    "idle",
    "navigating",
    "responding",
    "charging",
    "offline"
]

EMERGENCY_LEVELS = [
    "normal",
    "warning",
    "emergency",
    "critical"
]


# ======================================================
# UTILITY FUNCTIONS
# ======================================================

def get_device_by_id(device_id: str):
    """Get device configuration by device ID"""

    for device in DEVICES_TO_REGISTER:
        if device["device_id"] == device_id:
            return device

    return None


def get_all_device_ids() -> list:
    """Get all registered device IDs"""

    return [
        device["device_id"]
        for device in DEVICES_TO_REGISTER
    ]