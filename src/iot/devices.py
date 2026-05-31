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

DEVICES_TO_REGISTER = [

    # ==================================================
    # TEMPERATURE SENSOR
    # ==================================================
    {
        "device_id": "temp_sensor_a101",
        "entity_name": "Device:TEMP_A101",
        "entity_type": "TemperatureSensor",

        "attributes": [
            {"object_id": "t", "name": "temperature", "type": "Number"},
            {"object_id": "ts", "name": "TimeInstant", "type": "DateTime"}
        ],

        "static_attributes": [

            # Core
            {"name": "demo_run_id", "type": "Text", "value": DEMO_RUN_ID},
            {"name": "zone_id", "type": "Text", "value": ZONE_ID},
            {"name": "room_id", "type": "Text", "value": ZONE_ID},

            # Device info
            {"name": "unit", "type": "Text", "value": "°C"},
            {"name": "manufacturer", "type": "Text", "value": "DNTU IoT Lab"},
            {"name": "device_model", "type": "Text", "value": "DNTU-TEMP-V1"},
            {"name": "firmware_version", "type": "Text", "value": "1.0.0"},

            # Status
            {"name": "status", "type": "Text", "value": "online"},
            {"name": "connectivity", "type": "Text", "value": "connected"},
            {"name": "battery_level", "type": "Number", "value": 95},
            {"name": "signal_strength", "type": "Number", "value": -65},

            # Thresholds
            {"name": "normal_min", "type": "Number", "value": 22},
            {"name": "normal_max", "type": "Number", "value": 30},
            {"name": "warning_threshold", "type": "Number", "value": 35},
            {"name": "critical_threshold", "type": "Number", "value": 45},

            # Sensor config
            {"name": "sampling_rate_seconds", "type": "Number", "value": 5},
            {"name": "accuracy", "type": "Number", "value": 0.5},
            {"name": "calibration_status", "type": "Text", "value": "calibrated"},

            # Location
            {"name": "building_id", "type": "Text", "value": BUILDING_ID},
            {"name": "floor", "type": "Number", "value": 1},
            {"name": "installation_area", "type": "Text", "value": "Room A101"}
        ]
    },

    # ==================================================
    # HUMIDITY SENSOR
    # ==================================================
    {
        "device_id": "humid_sensor_a101",
        "entity_name": "Device:HUMID_A101",
        "entity_type": "HumiditySensor",

        "attributes": [
            {"object_id": "h", "name": "humidity", "type": "Number"},
            {"object_id": "ts", "name": "TimeInstant", "type": "DateTime"}
        ],

        "static_attributes": [

            # Core
            {"name": "demo_run_id", "type": "Text", "value": DEMO_RUN_ID},
            {"name": "zone_id", "type": "Text", "value": ZONE_ID},
            {"name": "room_id", "type": "Text", "value": ZONE_ID},

            # Device info
            {"name": "unit", "type": "Text", "value": "%"},
            {"name": "manufacturer", "type": "Text", "value": "DNTU IoT Lab"},
            {"name": "device_model", "type": "Text", "value": "DNTU-HUMID-V1"},
            {"name": "firmware_version", "type": "Text", "value": "1.0.0"},

            # Status
            {"name": "status", "type": "Text", "value": "online"},
            {"name": "connectivity", "type": "Text", "value": "connected"},
            {"name": "battery_level", "type": "Number", "value": 93},
            {"name": "signal_strength", "type": "Number", "value": -67},

            # Thresholds
            {"name": "normal_min", "type": "Number", "value": 40},
            {"name": "normal_max", "type": "Number", "value": 70},
            {"name": "warning_threshold", "type": "Number", "value": 80},
            {"name": "critical_threshold", "type": "Number", "value": 90},

            # Sensor config
            {"name": "sampling_rate_seconds", "type": "Number", "value": 5},
            {"name": "accuracy", "type": "Number", "value": 2},
            {"name": "calibration_status", "type": "Text", "value": "calibrated"},

            # Location
            {"name": "building_id", "type": "Text", "value": BUILDING_ID},
            {"name": "floor", "type": "Number", "value": 1},
            {"name": "installation_area", "type": "Text", "value": "Room A101"}
        ]
    },

    # ==================================================
    # AIR QUALITY SENSOR
    # ==================================================
    {
        "device_id": "air_sensor_a101",
        "entity_name": "Device:AIR_A101",
        "entity_type": "AirQualitySensor",

        "attributes": [
            {"object_id": "co2", "name": "co2", "type": "Number"},
            {"object_id": "ts", "name": "TimeInstant", "type": "DateTime"}
        ],

        "static_attributes": [

            # Core
            {"name": "demo_run_id", "type": "Text", "value": DEMO_RUN_ID},
            {"name": "zone_id", "type": "Text", "value": ZONE_ID},
            {"name": "room_id", "type": "Text", "value": ZONE_ID},

            # Device info
            {"name": "unit", "type": "Text", "value": "ppm"},
            {"name": "manufacturer", "type": "Text", "value": "DNTU IoT Lab"},
            {"name": "device_model", "type": "Text", "value": "DNTU-AIR-V1"},
            {"name": "firmware_version", "type": "Text", "value": "1.0.0"},

            # Status
            {"name": "status", "type": "Text", "value": "online"},
            {"name": "connectivity", "type": "Text", "value": "connected"},
            {"name": "battery_level", "type": "Number", "value": 92},
            {"name": "signal_strength", "type": "Number", "value": -66},

            # Thresholds
            {"name": "normal_min", "type": "Number", "value": 400},
            {"name": "normal_max", "type": "Number", "value": 900},
            {"name": "warning_threshold", "type": "Number", "value": 1200},
            {"name": "critical_threshold", "type": "Number", "value": 1800},

            # Sensor config
            {"name": "sampling_rate_seconds", "type": "Number", "value": 5},
            {"name": "accuracy", "type": "Number", "value": 5},
            {"name": "calibration_status", "type": "Text", "value": "calibrated"},

            # Location
            {"name": "building_id", "type": "Text", "value": BUILDING_ID},
            {"name": "floor", "type": "Number", "value": 1},
            {"name": "installation_area", "type": "Text", "value": "Room A101"}
        ]
    },

    # ==================================================
    # SMOKE DETECTOR
    # ==================================================
    {
        "device_id": "smoke_sensor_a101",
        "entity_name": "Device:SMOKE_A101",
        "entity_type": "SmokeDetector",

        "attributes": [
            {"object_id": "smoke", "name": "smoke_status", "type": "Number"},
            {"object_id": "ts", "name": "TimeInstant", "type": "DateTime"}
        ],

        "static_attributes": [

            # Core
            {"name": "demo_run_id", "type": "Text", "value": DEMO_RUN_ID},
            {"name": "zone_id", "type": "Text", "value": ZONE_ID},
            {"name": "room_id", "type": "Text", "value": ZONE_ID},

            # Device info
            {"name": "unit", "type": "Text", "value": "binary"},
            {"name": "manufacturer", "type": "Text", "value": "DNTU IoT Lab"},
            {"name": "device_model", "type": "Text", "value": "DNTU-SMOKE-V1"},
            {"name": "firmware_version", "type": "Text", "value": "1.0.0"},

            # Status
            {"name": "status", "type": "Text", "value": "online"},
            {"name": "connectivity", "type": "Text", "value": "connected"},
            {"name": "battery_level", "type": "Number", "value": 97},
            {"name": "signal_strength", "type": "Number", "value": -60},

            # Detection config
            {"name": "alarm_trigger_value", "type": "Number", "value": 1},
            {"name": "warning_threshold", "type": "Number", "value": 1},
            {"name": "critical_threshold", "type": "Number", "value": 1},

            # Safety config
            {"name": "sensor_sensitivity", "type": "Text", "value": "high"},
            {"name": "response_time_seconds", "type": "Number", "value": 2},
            {"name": "calibration_status", "type": "Text", "value": "calibrated"},
            {"name": "self_test_status", "type": "Text", "value": "passed"},

            # Sensor config
            {"name": "sampling_rate_seconds", "type": "Number", "value": 2},
            {"name": "power_source", "type": "Text", "value": "battery"},

            # Location
            {"name": "building_id", "type": "Text", "value": BUILDING_ID},
            {"name": "floor", "type": "Number", "value": 1},
            {"name": "installation_area", "type": "Text", "value": "Room A101 Ceiling"}
        ]
    },

    # ==================================================
    # SMART PLUG
    # ==================================================
    {
        "device_id": "smart_plug_a101",
        "entity_name": "Device:PLUG_A101",
        "entity_type": "SmartPlug",

        "attributes": [
            {"object_id": "energy", "name": "energy_consumption", "type": "Number"},
            {"object_id": "ts", "name": "TimeInstant", "type": "DateTime"}
        ],

        "static_attributes": [

            # Core
            {"name": "demo_run_id", "type": "Text", "value": DEMO_RUN_ID},
            {"name": "zone_id", "type": "Text", "value": ZONE_ID},
            {"name": "room_id", "type": "Text", "value": ZONE_ID},

            # Device info
            {"name": "unit", "type": "Text", "value": "W"},
            {"name": "manufacturer", "type": "Text", "value": "DNTU IoT Lab"},
            {"name": "device_model", "type": "Text", "value": "DNTU-PLUG-V1"},
            {"name": "firmware_version", "type": "Text", "value": "1.0.0"},

            # Status
            {"name": "status", "type": "Text", "value": "online"},
            {"name": "connectivity", "type": "Text", "value": "connected"},
            {"name": "signal_strength", "type": "Number", "value": -58},

            # Thresholds
            {"name": "normal_min", "type": "Number", "value": 50},
            {"name": "normal_max", "type": "Number", "value": 350},
            {"name": "warning_threshold", "type": "Number", "value": 450},
            {"name": "critical_threshold", "type": "Number", "value": 600},

            # Electrical config
            {"name": "voltage", "type": "Number", "value": 220},
            {"name": "max_current_amp", "type": "Number", "value": 10},
            {"name": "max_power_watt", "type": "Number", "value": 2200},
            {"name": "power_source", "type": "Text", "value": "AC"},

            # Smart features
            {"name": "remote_control_enabled", "type": "Boolean", "value": True},
            {"name": "overload_protection", "type": "Boolean", "value": True},
            {"name": "auto_shutdown_enabled", "type": "Boolean", "value": True},

            # Sensor config
            {"name": "sampling_rate_seconds", "type": "Number", "value": 5},
            {"name": "accuracy", "type": "Number", "value": 1.0},

            # Location
            {"name": "building_id", "type": "Text", "value": BUILDING_ID},
            {"name": "floor", "type": "Number", "value": 1},
            {"name": "installation_area", "type": "Text", "value": "Room A101 Wall Socket"}
        ]
    }
]


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