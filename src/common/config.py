import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

DEMO_RUN_ID = os.getenv("DEMO_RUN_ID", "DNTU02_TOP8_RUN_2026_001")
DEFAULT_ZONE_ID = os.getenv("DEFAULT_ZONE_ID", "DNTU_ROOM_A101")
DEFAULT_ROBOT_ID = os.getenv("DEFAULT_ROBOT_ID", "CRUZR_01")
ROBOT_ADAPTER = os.getenv("ROBOT_ADAPTER", "mock").lower()

ORION_URL = os.getenv("ORION_URL", "http://localhost:1026")
FIWARE_SERVICE = os.getenv("FIWARE_SERVICE", "openiot")
FIWARE_SERVICE_PATH = os.getenv("FIWARE_SERVICE_PATH", "/")

LOCAL_BRIDGE_URL = os.getenv("LOCAL_BRIDGE_URL", "http://localhost:8088/robot-action")
LOG_DIR = os.getenv("LOG_DIR", "logs")
MODEL_PATH = os.getenv("MODEL_PATH", "models/isolation_forest.joblib")
FEATURE_SCHEMA_PATH = os.getenv("FEATURE_SCHEMA_PATH", "models/feature_schema.json")

try:
    ORION_TIMEOUT = int(os.getenv("ORION_TIMEOUT_SECONDS", "5"))
except ValueError:
    ORION_TIMEOUT = 5

try:
    LOCAL_BRIDGE_TIMEOUT = int(os.getenv("LOCAL_BRIDGE_TIMEOUT_SECONDS", "5"))
except ValueError:
    LOCAL_BRIDGE_TIMEOUT = 5

# Validate critical configs
if not ORION_URL.startswith("http"):
    raise ValueError(f"Invalid ORION_URL configuration: {ORION_URL}")
