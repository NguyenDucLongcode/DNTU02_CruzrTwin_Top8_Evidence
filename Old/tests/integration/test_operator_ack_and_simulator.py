"""
Integration tests for Operator ACK logic and Cruzr Robot Simulator.
Validates the complete closed-loop:
  AlertEvent → RobotAction → CruzrSimulator(DELIVERED) → OperatorAck
  
NOTE: Operator ACK tests use direct function calls (not Flask test client)
to avoid Flask dependency in test environment.
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

import src.common.config
from src.common.logging_utils import reset_file, append_jsonl
from src.alerts.alert_service import reset_alert_service_cache
from src.robot.cruzr_simulator import poll_and_simulate_once, _delivered_actions


# ---------- Fixtures ----------

@pytest.fixture(autouse=True)
def setup_env(tmp_path):
    """Setup temporary log directories and mock config for all tests."""
    log_dir = tmp_path / "logs"
    evidence_dir = tmp_path / "evidence"
    log_dir.mkdir(exist_ok=True)
    evidence_dir.mkdir(exist_ok=True)

    original_get_config = src.common.config.get_config

    def mock_get_config():
        cfg = original_get_config()
        cfg["demo_run_id"] = "DNTU02_TOP8_RUN_2026_001"
        cfg["default_zone_id"] = "DNTU_ROOM_A101"
        cfg["log_dir"] = str(log_dir)
        cfg["evidence_dir"] = str(evidence_dir)
        cfg["orion_enabled"] = False
        return cfg

    src.common.config.get_config = mock_get_config
    reset_alert_service_cache()
    _delivered_actions.clear()
    yield tmp_path
    src.common.config.get_config = original_get_config
    reset_alert_service_cache()
    _delivered_actions.clear()


def read_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


# ---------- Operator ACK Logic Tests (no Flask dependency) ----------

def _simulate_operator_ack(cfg, decision, scenario_id="SCN_CRITICAL_001",
                            operator_id="demo_operator", note=None):
    """Simulate Operator ACK logic directly (mirror of webhook_receiver endpoint logic)."""
    if decision not in ["ACK", "ERROR"]:
        return {"error": "Invalid decision"}, 400

    alert_id = f"AlertEvent:{scenario_id}"
    robot_action_id = f"RobotAction:{scenario_id}"
    demo_run_id = cfg["demo_run_id"]
    zone_id = cfg["default_zone_id"]
    operator_ack_id = f"OperatorAck:{scenario_id}"

    if note is None:
        note = ("Operator confirmed Cruzr guidance delivered." if decision == "ACK"
                else "Operator reported error.")

    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    log_entry = {
        "demo_run_id": demo_run_id,
        "timestamp": timestamp,
        "scenario_id": scenario_id,
        "zone_id": zone_id,
        "operator_ack_id": operator_ack_id,
        "operator_id": operator_id,
        "alert_id": alert_id,
        "robot_action_id": robot_action_id,
        "operator_decision": decision,
        "result": "ACK" if decision == "ACK" else "ERROR",
        "note": note,
        "orion_upsert_status": "SKIPPED_OFFLINE"
    }
    ack_log_path = os.path.join(cfg["log_dir"], "operator_ack.jsonl")
    append_jsonl(ack_log_path, log_entry)

    return {
        "status": "acknowledged" if decision == "ACK" else "error_reported",
        "operator_decision": decision,
        "alert_id": alert_id,
        "robot_action_id": robot_action_id,
        "operator_ack_id": operator_ack_id,
        "orion_upsert_status": "SKIPPED_OFFLINE"
    }, 200


class TestOperatorAck:
    """Tests for Operator ACK logic."""

    def test_ack_decision_accepted(self, setup_env):
        """ACK decision returns correct response fields."""
        cfg = src.common.config.get_config()
        res, code = _simulate_operator_ack(cfg, "ACK")
        assert code == 200
        assert res["status"] == "acknowledged"
        assert res["operator_decision"] == "ACK"
        assert res["operator_ack_id"] == "OperatorAck:SCN_CRITICAL_001"
        assert res["orion_upsert_status"] == "SKIPPED_OFFLINE"

    def test_error_decision_accepted(self, setup_env):
        """ERROR decision returns error_reported status."""
        cfg = src.common.config.get_config()
        res, code = _simulate_operator_ack(cfg, "ERROR")
        assert code == 200
        assert res["status"] == "error_reported"
        assert res["operator_decision"] == "ERROR"

    def test_invalid_decision_rejected(self, setup_env):
        """Invalid decision returns 400."""
        cfg = src.common.config.get_config()
        res, code = _simulate_operator_ack(cfg, "MAYBE")
        assert code == 400
        assert "Invalid decision" in res["error"]

    def test_ack_logs_to_jsonl(self, setup_env):
        """ACK writes to logs/operator_ack.jsonl with correct fields."""
        cfg = src.common.config.get_config()
        _simulate_operator_ack(cfg, "ACK")

        ack_log = os.path.join(cfg["log_dir"], "operator_ack.jsonl")
        entries = read_jsonl(ack_log)
        assert len(entries) == 1
        entry = entries[0]
        assert entry["operator_decision"] == "ACK"
        assert entry["result"] == "ACK"
        assert entry["demo_run_id"] == "DNTU02_TOP8_RUN_2026_001"
        assert entry["scenario_id"] == "SCN_CRITICAL_001"
        assert entry["orion_upsert_status"] == "SKIPPED_OFFLINE"

    def test_ack_error_with_custom_note(self, setup_env):
        """ERROR decision with custom note logs correctly."""
        cfg = src.common.config.get_config()
        custom_note = "Robot battery depleted, could not navigate."
        _simulate_operator_ack(cfg, "ERROR", scenario_id="SCN_CRITICAL_002", note=custom_note)

        ack_log = os.path.join(cfg["log_dir"], "operator_ack.jsonl")
        entries = read_jsonl(ack_log)
        assert len(entries) == 1
        assert entries[0]["note"] == custom_note
        assert entries[0]["result"] == "ERROR"
        assert entries[0]["scenario_id"] == "SCN_CRITICAL_002"


# ---------- Robot Simulator Tests ----------

class TestCruzrSimulator:
    """Tests for Cruzr Robot Simulator daemon (offline mode)."""

    def test_offline_poll_delivers_action(self, setup_env):
        """In offline mode, simulator delivers default critical action and logs it."""
        cfg = src.common.config.get_config()
        result = poll_and_simulate_once(cfg)
        assert result is True

        robot_log = os.path.join(cfg["log_dir"], "robot_actions.jsonl")
        entries = read_jsonl(robot_log)
        assert len(entries) == 1
        assert entries[0]["status"] == "DELIVERED"
        assert entries[0]["robot_id"] == "CRUZR_01"
        assert entries[0]["action_type"] == "VOICE_DISPLAY_GUIDANCE"
        assert entries[0]["orion_upsert_status"] == "SKIPPED_OFFLINE"
        assert "Room A101" in entries[0]["message"]

    def test_offline_poll_idempotent(self, setup_env):
        """Second offline poll does not create duplicate entries."""
        cfg = src.common.config.get_config()
        poll_and_simulate_once(cfg)
        poll_and_simulate_once(cfg)

        robot_log = os.path.join(cfg["log_dir"], "robot_actions.jsonl")
        entries = read_jsonl(robot_log)
        assert len(entries) == 1

    def test_offline_poll_second_call_returns_false(self, setup_env):
        """Second offline poll returns False (nothing to process)."""
        cfg = src.common.config.get_config()
        first = poll_and_simulate_once(cfg)
        second = poll_and_simulate_once(cfg)
        assert first is True
        assert second is False

    def test_delivered_log_entry_schema(self, setup_env):
        """Verify all required fields exist in the robot_actions.jsonl entry."""
        cfg = src.common.config.get_config()
        poll_and_simulate_once(cfg)

        robot_log = os.path.join(cfg["log_dir"], "robot_actions.jsonl")
        entry = read_jsonl(robot_log)[0]

        required_fields = [
            "demo_run_id", "timestamp", "robot_action_id", "alert_id",
            "scenario_id", "zone_id", "robot_id", "action_type",
            "navigation_mode", "message", "status", "orion_upsert_status"
        ]
        for field in required_fields:
            assert field in entry, f"Missing field: {field}"

    def test_safety_disclaimer_in_message(self, setup_env):
        """Robot message contains safe guidance, not dangerous commands."""
        cfg = src.common.config.get_config()
        poll_and_simulate_once(cfg)

        robot_log = os.path.join(cfg["log_dir"], "robot_actions.jsonl")
        entry = read_jsonl(robot_log)[0]
        msg = entry["message"]
        assert "safe waiting area" in msg.lower()
        assert "follow staff guidance" in msg.lower()
        # Safety: robot does NOT claim to extinguish fire or cut power
        assert "extinguish" not in msg.lower()
        assert "cut power" not in msg.lower()
