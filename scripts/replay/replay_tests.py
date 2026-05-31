import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timezone
import requests

# Ensure repo root is on import path so `from src...` works when running scripts
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.utils.mqtt_helper import (
    create_mqtt_client,
    disconnect_mqtt_client,
    publish_scenario_with_client,
    _build_sensor_reading_entry,
    _classify_anomaly,
    _append_jsonl,
    SENSOR_READING_LOG,
    AI_DETECTION_LOG,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("replay_tests")


def load_test_files(test_dir: Path):
    return sorted(test_dir.glob("*.json"))


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def extract_device_values(payload: dict) -> dict:
    """Extract one sensor snapshot from replay payloads.

    Replay files store measurements under payload['readings'] as a time series.
    The replay flow uses the latest reading as the representative snapshot.
    """
    readings = payload.get("readings") or []
    latest = readings[-1] if readings else payload

    return {
        "temp_sensor_a101": latest.get("temperature") or latest.get("temp") or latest.get("temperature_c") or 0,
        "humid_sensor_a101": latest.get("humidity") or latest.get("humid") or 0,
        "air_sensor_a101": latest.get("co2") or latest.get("air_quality_or_co2") or latest.get("co2_ppm") or 0,
        "smoke_sensor_a101": latest.get("smoke_status") or latest.get("smoke") or 0,
        "smart_plug_a101": latest.get("energy_consumption") or latest.get("energy") or 0,
    }


def run_all(test_dir: Path, fimat_url: str, out_log: Path, pause: float = 1.0):
    files = load_test_files(test_dir)
    if not files:
        logger.error("No test files found in %s", test_dir)
        return 1

    out_log.parent.mkdir(parents=True, exist_ok=True)
    use_mqtt = os.getenv("REPLAY_USE_MQTT", "1").lower() in ("1", "true", "yes")
    mqtt_client = None

    if use_mqtt:
        mqtt_client = create_mqtt_client()

    try:
        with out_log.open("a", encoding="utf-8") as fh:
            for p in files:
                logger.info("Running test file: %s", p)
                payload = json.loads(p.read_text(encoding="utf-8"))

                # Update timestamp and demo_run_id for uniqueness
                payload["timestamp"] = now_iso()
                payload["demo_run_id"] = payload.get("demo_run_id") or f"TEST_{p.stem}_{int(time.time())}"

                entry = {
                    "test_file": str(p),
                    "sent_at": now_iso(),
                    "payload": payload,
                    "post_response": None,
                    "room_entity": None,
                }

                # Determine whether to use MQTT/FIMAT or run local-only processing

                # Build device_values from the latest reading in the time-series payload.
                device_values = extract_device_values(payload)

                scenario_name = f"REPLAY {p.stem}"
                scenario_id = payload.get("scenario_id") or payload.get("scenario") or p.stem.upper()

                if use_mqtt:
                    # Reuse a single MQTT connection for all files in the replay set.
                    try:
                        success = publish_scenario_with_client(
                            client=mqtt_client,
                            device_values=device_values,
                            scenario_name=scenario_name,
                            scenario_id_param=scenario_id,
                        )
                        entry["post_response"] = {"published_via_mqtt": bool(success)}
                    except Exception as e:
                        logger.exception("Publish via publish_scenario_with_client failed")
                        entry["post_response"] = {"error": str(e)}
                else:
                    # Local-only fast path: write sensor reading and AI detection logs without network I/O
                    try:
                        device_status = (
                            "CRITICAL" if "CRITICAL" in scenario_name.upper()
                            else "WARNING" if "WARNING" in scenario_name.upper()
                            else "NORMAL"
                        )

                        sensor_entry = _build_sensor_reading_entry(
                            device_values=device_values,
                            scenario_id=scenario_id,
                            demo_run_id=os.getenv("DEMO_RUN_ID", "DNTU02_TOP8_RUN_2026_001"),
                            zone_id=os.getenv("ZONE_ID", "DNTU_ROOM_A101"),
                            device_status=device_status,
                        )
                        _append_jsonl(SENSOR_READING_LOG, sensor_entry)

                        ai_entry = {
                            "demo_run_id": os.getenv("DEMO_RUN_ID", "DNTU02_TOP8_RUN_2026_001"),
                            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                            "scenario_id": scenario_id,
                            "zone_id": os.getenv("ZONE_ID", "DNTU_ROOM_A101"),
                            **_classify_anomaly(device_values, device_status.lower()),
                        }
                        _append_jsonl(AI_DETECTION_LOG, ai_entry)

                        entry["post_response"] = {"local_processed": True}
                    except Exception as e:
                        logger.exception("Local processing failed")
                        entry["post_response"] = {"error": str(e)}

                # Small pause to allow Orion update
                time.sleep(pause)

                # Try to fetch Room entity via FIMAT debugging endpoint only when network lookup is desired.
                if not use_mqtt:
                    try:
                        zone = payload.get("zone_id")
                        if zone:
                            get_url = f"{fimat_url.rstrip('/')}/v1/orion/entities/Room:{zone}"
                            r2 = requests.get(get_url, timeout=8)
                            try:
                                entry["room_entity"] = {"status_code": r2.status_code, "json": r2.json()}
                            except Exception:
                                entry["room_entity"] = {"status_code": r2.status_code, "text": r2.text}
                        else:
                            entry["room_entity"] = {"error": "no zone_id"}
                    except Exception as e:
                        logger.exception("GET Room entity failed")
                        entry["room_entity"] = {"error": str(e)}
                else:
                    entry["room_entity"] = {"skipped": True}

                # Write one-line JSON record to log
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
                fh.flush()

    finally:
        if mqtt_client is not None:
            disconnect_mqtt_client(mqtt_client)

    logger.info("Replay completed, results appended to %s", out_log)
    return 0


if __name__ == "__main__":
    test_dir = Path(os.getenv("TEST_DIR", "data/replay_test_set"))
    fimat_url = os.getenv("FIMAT_API_URL", "http://localhost:8080")
    # Prefer an explicit ORION_URL if provided (Orion NGSI v2)
    orion_url = os.getenv("ORION_URL", None)
    if orion_url:
        logger.info("Using ORION_URL=%s for Room lookups", orion_url)
    else:
        logger.info("No ORION_URL set; using FIMAT_API_URL=%s for Room lookups", fimat_url)
    out_log = Path(os.getenv("OUT_LOG", "logs/replay_results.jsonl"))
    exit(run_all(test_dir, fimat_url, out_log))
