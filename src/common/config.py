import os
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

def get_config() -> dict:
    """
    Get configuration dictionary from environment variables or defaults.
    No absolute paths are used.
    """
    return {
        "demo_run_id": os.getenv("DEMO_RUN_ID", "DNTU02_TOP8_RUN_2026_001"),
        "default_zone_id": os.getenv("DEFAULT_ZONE_ID", "DNTU_ROOM_A101"),
        "data_path": os.getenv("DATA_PATH", "data/sensor_data.csv"),
        "model_path": os.getenv("MODEL_PATH", "models/anomaly_model.pkl"),
        "feature_schema_path": os.getenv("FEATURE_SCHEMA_PATH", "models/feature_schema.json"),
        "log_dir": os.getenv("LOG_DIR", "logs"),
        "evidence_dir": os.getenv("EVIDENCE_DIR", "evidence"),
        "orion_enabled": os.getenv("ORION_ENABLED", "false").lower() == "true",
        "closed_loop_enabled": os.getenv("CLOSED_LOOP_ENABLED", "true").lower() == "true"
    }
