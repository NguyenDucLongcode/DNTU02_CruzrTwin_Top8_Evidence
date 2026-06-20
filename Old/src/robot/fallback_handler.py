import os
import time
import requests

from .cruzr_client import CruzrRobotClient


def call_operator_error(
    alert_id: str,
    robot_action_id: str,
    zone_id: str,
    demo_run_id: str
):
    """
    Gọi API operator ACK với decision=ERROR
    """
    url = os.getenv(
        "OPERATOR_ACK_URL",
        "http://127.0.0.1:5000/api/operator/ack"
    )

    scenario_id = alert_id.replace(
        "AlertEvent:",
        ""
    )

    payload = {
        "decision": "ERROR",
        "alert_id": alert_id,
        "robot_action_id": robot_action_id,
        "operator_id": "system_auto",
        "demo_run_id": demo_run_id,
        "scenario_id": scenario_id,
        "zone_id": zone_id,
        "note": "Robot unavailable after 3 retries"
    }

    try:
        print("   📡 Calling operator ACK API...")

        response = requests.post(
            url,
            json=payload,
            timeout=5
        )

        print(f"   📡 Status: {response.status_code}")

        try:
            print(response.json())
        except Exception:
            print(response.text)

        return {
            "success": response.status_code == 200,
            "status_code": response.status_code
        }

    except Exception as e:
        print(f"   ❌ Operator ACK API error: {e}")

        return {
            "success": False,
            "error": str(e)
        }


def try_robot_connection(
    zone_id: str,
    alert_id: str,
    robot_action_id: str,
    demo_run_id: str,
    max_retries: int = 3
):
    """
    Kiểm tra kết nối robot.
    Nếu thành công trả về luôn object robot.
    """
    for attempt in range(1, max_retries + 1):
        print(f"   🤖 Attempt {attempt}/{max_retries}")

        try:
            robot_client = CruzrRobotClient()

            if robot_client.connect():
                print("   ✅ Robot connection success")

                return {
                    "success": True,
                    "robot_connected": True,
                    "robot": robot_client,      # <-- QUAN TRỌNG
                    "retries": attempt,
                    "operator_ack": None
                }

            print("   ❌ Robot connect failed")

        except Exception as e:
            print(f"   ❌ Error: {e}")

        if attempt < max_retries:
            time.sleep(2)

    print(f"   ❌ Robot failed after {max_retries} attempts")

    operator_ack = call_operator_error(
        alert_id=alert_id,
        robot_action_id=robot_action_id,
        zone_id=zone_id,
        demo_run_id=demo_run_id
    )
    return {
        "success": False,
        "robot_connected": False,
        "retries": max_retries,
        "operator_ack": operator_ack
    }