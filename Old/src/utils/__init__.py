"""
Utils Module - Các hàm tiện ích dùng chung
"""

from .mqtt_helper import (
    create_mqtt_client,
    disconnect_mqtt_client,
    publish_device_data,
    publish_multiple_devices,
    publish_scenario,
    DEFAULT_MQTT_BROKER,
    DEFAULT_MQTT_PORT,
    DEFAULT_APIKEY,
    DEFAULT_DEMO_RUN_ID,
    DEFAULT_ZONE_ID,
)

from .translator_utils import (
    translate_to_vietnamese,
    translate_to_english,
    translate,
    clear_cache,
    get_cache_size,
    is_translator_available,
    test_translator
)

from .log_helper import write_orion_state_log

from .replay_helpers import (
    load_test_files,
    now_iso,
    extract_all_readings,
   extract_device_values_from_reading,
    extract_sequence_number,
    extract_scenario_type,
    build_scenario_id,
    get_device_status_from_filename,
)

from .speak_helper import (
    speak_and_wait,
    speak_sequence,
    speak_simple,
    estimate_speak_duration,
    wait_for_robot_ready
)

__all__ = [
    # MQTT helpers
    "create_mqtt_client",
    "disconnect_mqtt_client", 
    "publish_device_data",
    "publish_multiple_devices",
    "publish_scenario",
    "DEFAULT_MQTT_BROKER",
    "DEFAULT_MQTT_PORT", 
    "DEFAULT_APIKEY",
    "DEFAULT_DEMO_RUN_ID",
    "DEFAULT_ZONE_ID",
    
    # Replay helpers
    "load_test_files",
    "now_iso",
    "extract_all_readings",
    "extract_device_values_from_reading",
    "extract_sequence_number",
    "extract_scenario_type",
    "build_scenario_id",
    "get_device_status_from_filename",

    # Log helpers
    "write_orion_state_log"

    # Translator utils
    "translate_to_vietnamese",
    "translate_to_english",
    "translate",
    "clear_cache",
    "get_cache_size",
    "is_translator_available",
    "test_translator"

    # Speak helpers
    "speak_and_wait",
    "speak_sequence",
    "speak_simple",
    "estimate_speak_duration",
    "wait_for_robot_ready"
]