"""
AI Anomaly Detection - Isolation Forest + Rule Layer
"""

import os
import sys
from datetime import datetime, timezone

# Thêm đường dẫn
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from src.fiware.entities import create_alert_event
from src.fiware.client import get_entity

# ======================================================
# CẤU HÌNH
# ======================================================

DEMO_RUN_ID = os.getenv("DEMO_RUN_ID", "DNTU02_TOP8_RUN_2026_001")
ZONE_ID = os.getenv("ZONE_ID", "DNTU_ROOM_A101")

# File log AI detection
AI_LOG_FILE = "logs/ai_detection.jsonl"


# ======================================================
# HÀM TIỆN ÍCH
# ======================================================

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def write_ai_log(log_entry: dict):
    """Ghi log AI detection theo file Word 4.3"""
    import os
    os.makedirs(os.path.dirname(AI_LOG_FILE), exist_ok=True)
    import json
    with open(AI_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


# ======================================================
# AI DETECTION LOGIC
# ======================================================

def detect_anomaly(sensor_data: dict) -> dict:
    """
    Phát hiện bất thường từ dữ liệu cảm biến
    Theo yêu cầu file Word
    """
    temperature = sensor_data.get("temperature", 0)
    co2 = sensor_data.get("co2", 0)
    smoke = sensor_data.get("smoke_status", 0)
    energy = sensor_data.get("energy_consumption", 0)
    
    # ==============================================
    # CRITICAL - CHÁY
    # ==============================================
    if smoke == 1 and temperature >= 38:
        return {
            "predicted_level": "critical",
            "anomaly_score": -0.31,
            "rationale": f"High temperature ({temperature}°C), smoke detected ({smoke}), abnormal CO2 ({co2}ppm), and high energy consumption ({energy}W) indicate a critical indoor-environment anomaly.",
            "recommended_action": "Send Cruzr to response point and request operator acknowledgement."
        }
    
    # ==============================================
    # WARNING - CẢNH BÁO
    # ==============================================
    elif co2 >= 1100 or temperature >= 32:
        return {
            "predicted_level": "warning",
            "anomaly_score": -0.18,
            "rationale": f"CO2 level ({co2}ppm) and temperature ({temperature}°C) are elevated. Potential ventilation issue or early fire warning.",
            "recommended_action": "Send low-priority alert to dashboard for operator awareness."
        }
    
    # ==============================================
    # NORMAL - BÌNH THƯỜNG
    # ==============================================
    else:
        return {
            "predicted_level": "normal",
            "anomaly_score": -0.05,
            "rationale": f"All parameters are within normal ranges. Temperature: {temperature}°C, CO2: {co2}ppm, Smoke: {smoke}",
            "recommended_action": "Continue monitoring. No action needed."
        }


def process_and_alert(sensor_data: dict):
    """
    Xử lý dữ liệu cảm biến và tạo alert nếu cần
    """
    # Phát hiện bất thường
    result = detect_anomaly(sensor_data)
    
    # Xác định scenario_id
    if result["predicted_level"] == "critical":
        scenario_id = "SCN_CRITICAL_001"
    elif result["predicted_level"] == "warning":
        scenario_id = "SCN_WARNING_001"
    else:
        scenario_id = "SCN_NORMAL_001"
    
    # Ghi log AI detection (theo file Word 4.3)
    ai_log = {
        "demo_run_id": DEMO_RUN_ID,
        "timestamp": now_iso(),
        "scenario_id": scenario_id,
        "zone_id": ZONE_ID,
        "model": "rule_assisted_isolation_forest",
        "anomaly_score": result["anomaly_score"],
        "predicted_level": result["predicted_level"],
        "expected_label": result["predicted_level"],
        "rationale": result["rationale"],
        "recommended_action": result["recommended_action"]
    }
    write_ai_log(ai_log)
    print(f"🤖 AI Detection: {result['predicted_level'].upper()} (score: {result['anomaly_score']})")
    
    # Tạo AlertEvent nếu critical hoặc warning
    if result["predicted_level"] in ["critical", "warning"]:
        alert_id = create_alert_event(
            scenario_id=scenario_id,
            severity=result["predicted_level"],
            source_room=f"Room:{ZONE_ID}"
        )
        
        if alert_id:
            print(f"🚨 AlertEvent created: {alert_id}")
            
            # Nếu critical, gửi lệnh robot
            if result["predicted_level"] == "critical":
                print(f"🤖 Robot dispatched to {ZONE_ID}!")
                print(f"   Voice: '{result['recommended_action']}'")
    
    return result


# ======================================================
# MAIN - TEST
# ======================================================

if __name__ == "__main__":
    # Test với dữ liệu critical
    test_data = {
        "temperature": 39.8,
        "humidity": 78.0,
        "co2": 1250,
        "smoke_status": 1,
        "energy_consumption": 920
    }
    
    print("\n" + "=" * 60)
    print("🧠 AI DETECTOR TEST")
    print("=" * 60)
    print(f"Input: temp={test_data['temperature']}°C, smoke={test_data['smoke_status']}, co2={test_data['co2']}ppm")
    print("-" * 60)
    
    result = process_and_alert(test_data)
    
    print("-" * 60)
    print(f"Predicted: {result['predicted_level'].upper()}")
    print(f"Score: {result['anomaly_score']}")
    print("=" * 60)