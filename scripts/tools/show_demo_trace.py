"""Show the closed-loop demo trace in one command.

Order:
SensorReading -> Orion state -> AI detection -> AlertEvent -> RobotAction -> OperatorAck
"""

import argparse
import json
import os
from pathlib import Path
from typing import Any, Optional

DEFAULT_DEMO_RUN_ID = os.getenv("DEMO_RUN_ID", "DNTU02_TOP8_RUN_2026_001")
DEFAULT_SCENARIO_ID = "SCN_CRITICAL_001"
DEFAULT_ZONE_ID = os.getenv("ZONE_ID", "DNTU_ROOM_A101")

LOG_DIR = Path("logs")
SENSOR_LOG = LOG_DIR / "sensor_readings.jsonl"
AI_LOG = LOG_DIR / "ai_detection.jsonl"
ORION_LOG = LOG_DIR / "orion_state.jsonl"
ROBOT_LOG = LOG_DIR / "robot_action.jsonl"
ACK_LOG = LOG_DIR / "operator_ack.jsonl"


def load_jsonl_lines(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    rows = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def matches(entry: dict[str, Any], demo_run_id: str, scenario_id: str, zone_id: str) -> bool:
    return (
        entry.get("demo_run_id") == demo_run_id
        and entry.get("scenario_id") == scenario_id
        and entry.get("zone_id") == zone_id
    )


def latest_matching(entries: list[dict[str, Any]], demo_run_id: str, scenario_id: str, zone_id: str) -> Optional[dict[str, Any]]:
    for entry in reversed(entries):
        if matches(entry, demo_run_id, scenario_id, zone_id):
            return entry
    return None


def print_section(title: str, entry: Optional[dict[str, Any]], evidence_path: Path):
    print(f"\n=== {title} ===")
    print(f"Evidence: {evidence_path}")
    if entry is None:
        print("MISSING")
        return
    print(json.dumps(entry, ensure_ascii=False, indent=2))


def build_alert_from_orion(orion_entry: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if not orion_entry:
        return None

    alerts = orion_entry.get("alerts") or []
    for alert in reversed(alerts):
        if alert.get("type") == "AlertEvent":
            return alert
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Print the closed-loop demo trace from JSONL logs.")
    parser.add_argument("--demo-run-id", default=DEFAULT_DEMO_RUN_ID)
    parser.add_argument("--scenario-id", default=DEFAULT_SCENARIO_ID)
    parser.add_argument("--zone-id", default=DEFAULT_ZONE_ID)
    args = parser.parse_args()

    sensor_entries = load_jsonl_lines(SENSOR_LOG)
    ai_entries = load_jsonl_lines(AI_LOG)
    orion_entries = load_jsonl_lines(ORION_LOG)
    robot_entries = load_jsonl_lines(ROBOT_LOG)
    ack_entries = load_jsonl_lines(ACK_LOG)

    sensor = latest_matching(sensor_entries, args.demo_run_id, args.scenario_id, args.zone_id)
    ai = latest_matching(ai_entries, args.demo_run_id, args.scenario_id, args.zone_id)
    orion = latest_matching(orion_entries, args.demo_run_id, args.scenario_id, args.zone_id)
    alert = build_alert_from_orion(orion)
    robot = latest_matching(robot_entries, args.demo_run_id, args.scenario_id, args.zone_id)
    ack = latest_matching(ack_entries, args.demo_run_id, args.scenario_id, args.zone_id)

    print("=" * 72)
    print("DEMO TRACE")
    print("=" * 72)
    print(f"demo_run_id: {args.demo_run_id}")
    print(f"scenario_id: {args.scenario_id}")
    print(f"zone_id    : {args.zone_id}")

    print_section("1. SensorReading", sensor, SENSOR_LOG)
    print_section("2. Orion state", orion, ORION_LOG)
    print_section("3. AI detection", ai, AI_LOG)
    print_section("4. AlertEvent", alert, ORION_LOG)
    print_section("5. RobotAction", robot, ROBOT_LOG)
    print_section("6. OperatorAck", ack, ACK_LOG)

    print("\n" + "=" * 72)
    return 0 if all([sensor, ai, orion, alert, robot, ack]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
